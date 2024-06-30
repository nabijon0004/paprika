import datetime
import random

from django.db import connections
from redis import AuthenticationError
from authentification.kannelSMS import sendSMS

from . import models


def generate_otp(p_msisdn):
    '''for genereting and sendig sms to clients
    '''
    otp_value = str(random.randint(10000, 99999))
    print(p_msisdn, '', otp_value)
    sendSMS(p_msisdn, otp_value)
    return otp_value


def generate_txn():
    '''for generating txn (random number for not sending clint msisdn) value
    '''
    return random.randint(100000, 999999)

def validate_otp(p_otp_value, p_txn_value, p_msisdn_value):
    '''Checkig acctul otp to to given one
    '''
    OTP_PERIOD_ACCESSIBILITY = 50000 #minuts
    OTP_EXIRED_CODE = 452
    OTP_INCORRECT_CODE = 453
    AUTH_NOT_FOUD = 454
    SUCCESS_CODE = 100

    actual_opt_data = models.AuthenCredentianls.objects\
        .filter(txn_value = p_txn_value, otp_value = p_otp_value, msisdn = p_msisdn_value,end_date=None, end_reason=None)\
        .values('start_date','otp_value','msisdn')

    
    try:
        actual_otp_time = actual_opt_data[0]['start_date']
        actual_otp_value = actual_opt_data[0]['otp_value']
        actual_msisdn = actual_opt_data[0]['msisdn']
    except:
        return (AUTH_NOT_FOUD, {"Message":"Authentication data not found!"})

        
    time_delta_otp = (datetime.datetime.now() - actual_otp_time.replace(tzinfo=None)).total_seconds()/60
    print ('time_delta_otp:')
    print (time_delta_otp)
    if OTP_PERIOD_ACCESSIBILITY < time_delta_otp:
        return (OTP_EXIRED_CODE, {"Message":"OTP expired"}) 
    if actual_otp_value != int(p_otp_value):
        return (OTP_INCORRECT_CODE, {"Message":"Incorrect OTP"})    
    return (SUCCESS_CODE, actual_msisdn)

def get_subs_id(msisdn):
    print ('line 47')
    with connections['ppcdb'].cursor() as cursor:
        cursor.execute("""Select subs_id from subs_list_view where msisdn='""" + str(msisdn) + "'")
        columns2 = [i[0] for i in cursor.description]
        block=[dict(zip(columns2, row)) for row in cursor]
        check_block=block[0]['SUBS_ID']  
        #cursor.execute(f"select subs_id from subs_list_view where msisdn={str(msisdn)};")

    return cursor