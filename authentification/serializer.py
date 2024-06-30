from rest_framework import serializers
from .models import AuthenCredentianls
class SendCode(serializers.Serializer):
    phone = serializers.CharField(required=True, max_length = 12, min_length = 12)
    device_token = serializers.CharField(default="not token")


class CheckSentCode(serializers.Serializer):
    txn_id = serializers.CharField(required=True)
    sms_code = serializers.CharField(required=True)

class AuthenCredentianlsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AuthenCredentianls
        fields = (
            'msisdn',
            'subs_id',
            'otp_value', 
            'txn_value', 
            'start_date', 
            'device_model', 
            'device_os',
            'device_ip',
            'device_token')

class OTP(serializers.Serializer):
    phone = serializers.CharField(max_length=12, min_length=12)

class VerifyOTP(serializers.Serializer):
    stt = serializers.CharField(max_length=256)
    otp = serializers.IntegerField()
    phone = serializers.CharField(max_length=12, min_length=12)
    device_model = serializers.CharField(max_length=100)
    device_os = serializers.CharField(max_length=50)
    # device_ip = serializers.CharField(max_length=15)
class Refresh(serializers.Serializer):
    refresh = serializers.CharField(max_length=256)