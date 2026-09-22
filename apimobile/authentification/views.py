import logging
import os
import random

from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentification import docs, serializer, token
from authentification.models import AuthHistory
from authentification.utils.filter import filtering
from .auth_decorators import auth_required
from .db import send_sms as send_sms_db
from .models import sent_code, check_sent_code, logout

logger = logging.getLogger(__name__)

# Тестовый номер для проверки приложения в сторах: OTP не проверяется.
# Задаётся через окружение, чтобы не быть постоянным обходом авторизации.
DEV_TEST_MSISDN = os.environ.get("DEV_TEST_MSISDN", "")
DEV_TEST_TOKEN = os.environ.get("DEV_TEST_TOKEN", "")
class SendCode(APIView):

    @docs.send_code
    def post(self, request):
        validation = serializer.SendCode(data=request.data)
        if validation.is_valid(raise_exception=True):
            return filtering(
                sent_code(
                    request, 
                    phone=validation.data['phone'], 
                    device_token=validation.data['device_token']
                    )
            )
        else:
            return Response({"message":"Bad request"}, status=status.HTTP_400_BAD_REQUEST)
CHECK_SENT_CODE_ERRORS = {
    "22001": "Токен некорректный",
    "22002": "Токен уже используется",
    "22004": "Токен уже используется",
    "22003": "Срок действия txn_id уже истек. Время его жизни составляет 15 минут.",
    "22005": "Срок действия txn_id уже истек. Время его жизни составляет 15 минут.",
    "22006": "Слишком много попыток подтверждения через SMS-код",
    "22007": "Неверный SMS-код",
    "22008": "OK",
}


class CheckSentCode(APIView):

    @docs.check_sent_code
    def post(self, request):
        validation = serializer.CheckSentCode(data=request.data)

        if validation.is_valid(raise_exception=True):
            result = check_sent_code(
                request,
                txn_id=validation.data['txn_id'],
                sms_code=validation.data['sms_code']
            )

            response = filtering(result)

            data = result.get("data", {}) if isinstance(result, dict) else {}
            exit_location_id = (
                result.get("exit_location_id")
                if isinstance(result, dict)
                else None
            ) or data.get("exit_location_id")

            err_msg = CHECK_SENT_CODE_ERRORS.get(str(exit_location_id))
            if err_msg is not None and isinstance(response.data, dict):
                response.data["err_msg"] = err_msg

            response.status_code = (
                status.HTTP_200_OK
                if str(exit_location_id) == "22008"
                else status.HTTP_401_UNAUTHORIZED
            )

            return response

        return Response(
            {"message": "Bad request"},
            status=status.HTTP_400_BAD_REQUEST
        )

class Logout(APIView):
    
    @docs.logoff_get
    def get(self, request):
        res = logout(request)
        return filtering(res)
    
    @docs.logoff_post
    def post(self, request):
        res = logout(request)
        return filtering(res)
class OTP(APIView):
    
    def send_sms(self, phone, otp: int):
        return send_sms_db(phone, "Код: "+str(otp))
    
    def create_stt(self, phone):
        
        created_time = timezone.now() - timezone.timedelta(minutes=15)
        history = AuthHistory.objects.filter(phone=phone, create_date__gte = created_time)
        if history.count() <= 5:
            random_otp = random.randint(10000, 99999)
            stt = token.generate_stt(otp=random_otp)
            auth_history = AuthHistory.objects.create(
                phone = phone,
                otp = random_otp,
                active = False,
                token = ""
                )
            if self.send_sms(phone, random_otp):

                auth_history.save()
                result = {
                    "status":"success",
                    "message":"OTP sent with SMS", 
                    "data":{
                            "stt": stt
                        }
                    }
            else:
                result = {"status":"error","message":"OTP sending error, please try again"}
        else:
            result = {"status":"error","message":"Try after 15 minutes"}
        
        return result

    @docs.hidden
    def post(self, request):
        valid_data = serializer.OTP(data=request.data)
        valid_data.is_valid(raise_exception=True)
        phone = valid_data.data.get('phone')

        result = self.create_stt(phone)
        return filtering(result)

class VerifyOTP(APIView):
    @docs.hidden
    def post(self, request):
        valid_data = serializer.VerifyOTP(data=request.data)
        valid_data.is_valid(raise_exception=True)
        phone = valid_data.data.get('phone')
        stt = valid_data.data.get('stt')
        otp = valid_data.data.get('otp')
        device_model = valid_data.data.get('device_model')
        device_os = valid_data.data.get('device_os')
        device_ip = valid_data.data.get('device_ip')

        if DEV_TEST_MSISDN and DEV_TEST_TOKEN and phone == DEV_TEST_MSISDN:
            logger.warning("Вход по тестовому номеру без проверки OTP")
            return filtering({
                "status": "success",
                "message": "Token generated (test)",
                "data": {"token": DEV_TEST_TOKEN, "branch_id": 4},
            })

        stt_decoded = token.decode(stt)
        if not stt_decoded['success']:
            return Response({"message": "Token is invalid or expired"},
                            status=status.HTTP_401_UNAUTHORIZED)
        if stt_decoded['otp'] != otp:
            return filtering({"status": "error", "message": "Invalid OTP"})

        # запись создаётся в OTP.create_stt; без неё подтверждать нечего
        auth_history = AuthHistory.objects.filter(phone=phone, otp=otp).last()
        if auth_history is None:
            return Response({"message": "Authentication data not found"},
                            status=status.HTTP_401_UNAUTHORIZED)

        AuthHistory.objects.filter(phone=phone, active=True).update(active=False)
        new_token = token.generate_refresh(phone=phone)
        access_token = token.generate_access(phone=phone)
        auth_history.token = new_token
        auth_history.verified = True
        auth_history.active = True
        auth_history.device_model = device_model
        auth_history.device_os = device_os
        auth_history.device_ip = device_ip
        auth_history.save()
        return filtering({
            "status": "success",
            "message": "Token generated",
            "data": {"refresh": new_token, "access-token": access_token},
        })
    
class Refresh(APIView):
    @docs.hidden
    def post(self, request):
        valid_data = serializer.Refresh(data=request.data)
        valid_data.is_valid(raise_exception=True)
        refresh = valid_data.data.get('refresh')
        stt_decoded = token.decode(refresh)
        if stt_decoded['success']:
            phone = stt_decoded['number']
            auth_history = AuthHistory.objects.filter(phone=phone, active = True, token = refresh).first()
            if auth_history:
                
                new_token = token.generate_refresh(phone=phone)
                access_token = token.generate_access(phone=phone)
                auth_history.token = new_token
                auth_history.save()
                result = {
                    "status":"success",
                    "message":"Token generated", 
                    "data": {
                        "refresh": new_token,
                        "access-token": access_token,
                        }
                    }
            else:
                return Response({"message":"Invalid refresh"}, status=status.HTTP_401_UNAUTHORIZED)              
        else:
            result = {"status":"error","message":"Invalid OTP"}
        
       
        return filtering(result)
    
@auth_required(token_only=True)
def deactivate_user(request, msisdn, auth_token):
    auth_history = AuthHistory.objects.filter(phone=msisdn, active = True).first()
    if auth_history:
        auth_history.active = False
        auth_history.save()
    return {
                    "status":"success",
                    "message":"Logout success", 
                    }
class LogOut(APIView):
    
    
    @docs.hidden
    def get(self, request):
        result = deactivate_user(request)
        return filtering(result)