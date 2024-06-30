import jwt
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings

def generate_refresh(phone: str):
    dt = timezone.now() + timezone.timedelta(days = 30)
    token = jwt.encode({
            'number': phone,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')
    return token

def generate_access(phone: str):
    dt = datetime.now() + timedelta(minutes = 600)
    token = jwt.encode({
            'phone': phone,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')
    return token

def generate_stt(otp: int):
    dt = datetime.now() + timedelta(minutes = 8)
    token = jwt.encode({
            'otp': otp,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')
    return token

def decode(token: str):
    try:
        res = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        res['success'] = True
        return res
    except jwt.ExpiredSignatureError:
        return {"success":False, "status":"error", "message":"Token life time expired"}
    except:
        return {"success":False, "status":"error", "message":"Invalid token"}