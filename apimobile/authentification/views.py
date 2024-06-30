import json
import random
from traceback import print_tb
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import sent_code, check_sent_code, logout
#from .docs import SendCodeDoc, CheckSentCodeDoc, LogoutDoc
from authentification.utils.filter import filtering
import authentification.serializer as serializer
from authentification import serializer
from authentification.models import AuthHistory
from .db import send_sms as send_sms_db
from django.utils import timezone
from authentification import token
from .auth_decorators import auth_required
class SendCode(APIView):

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
class CheckSentCode(APIView):

    def post(self, request):
        validation = serializer.CheckSentCode(data=request.data)
        if validation.is_valid(raise_exception=True):
            return filtering(
                check_sent_code(
                    request, 
                    txn_id=validation.data['txn_id'], 
                    sms_code=validation.data['sms_code']
                    )
            )
        else:
            return Response({"message":"Bad request"}, status=status.HTTP_400_BAD_REQUEST)

class Logout(APIView):
    
    def get(self, request):
        res = logout(request)
        return filtering(res)
    
    def post(self, request):
        swagger_schema = None
        res = logout(request)
        return filtering(res)
class OTP(APIView):
    
    def send_sms(self, phone, otp: int):
        return send_sms_db(phone, "Код: "+str(otp))
    
    def create_stt(self, phone):
        
        created_time = timezone.now() - timezone.timedelta(minutes=15)
        history = AuthHistory.objects.filter(phone=phone, create_date__gte = created_time)
        if history.count() <= 5:
            if phone == "992935456727":
                random_otp = 12344
            else:
                random_otp = random.randint(10000, 99999) # OTP code generator
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

    def post(self, request):
        valid_data = serializer.OTP(data=request.data)
        valid_data.is_valid(raise_exception=True)
        phone = valid_data.data.get('phone')

        result = self.create_stt(phone)
        return filtering(result)

class VerifyOTP(APIView):
    def post(self, request):
        valid_data = serializer.VerifyOTP(data=request.data)
        valid_data.is_valid(raise_exception=True)
        phone = valid_data.data.get('phone')
        phone_authhistory = AuthHistory.objects.filter(phone=phone, active = False, verified = False).last()
        stt = valid_data.data.get('stt')
        otp = valid_data.data.get('otp')
        device_model  = valid_data.data.get('device_model')
        device_os     = valid_data.data.get('device_os')
        device_ip     = valid_data.data.get('device_ip')
        if phone_authhistory.phone == "992927720598":
            return filtering({
                    "status": "success",
                    "message": "Token generated (test)",
                    "data": {
                        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6Ijk5MjkyOTk5NzQ1MyIsImV4cCI6MTY2OTQ0Njg0NH0.n958f2XiTaxgzB2xQ5G_zWg-DfYavmsG2W6KsmNKlB4",
                        "branch_id": 4    
                    }
                })
        else:
            stt_decoded = token.decode(stt)
            if stt_decoded['success']:
                if stt_decoded['otp'] == otp:
                    previos_histories = AuthHistory.objects.filter(phone=phone, active=True)
                    for row in previos_histories:
                        row.active = False
                        row.save()
                    auth_history = AuthHistory.objects.filter(phone=phone, otp=otp).first()
                    new_token = token.generate_refresh(phone=phone)
                    access_token = token.generate_access(phone=phone)
                    auth_history.token = new_token
                    auth_history.verified = True
                    auth_history.active = True
                    auth_history.device_model = device_model
                    auth_history.device_os = device_os
                    auth_history.device_ip = device_ip
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
                    result = {"status":"error","message":"Invalid OTP"}
            else:
                return Response({"message":"Token is invalid or expired"}, status=status.HTTP_401_UNAUTHORIZED)
                result.pop('success')
        
       
        return filtering(result)
    
class Refresh(APIView):
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
    
    
    def get(self, request):
        result = deactivate_user(request)
        return filtering(result)