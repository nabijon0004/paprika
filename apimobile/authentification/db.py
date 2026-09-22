"""
Доступ к БД авторизации: хранимые процедуры и отправка SMS.
"""
import json
import logging
import os
import sys

import requests
from django.db import connections
from django.utils import translation

from authentification.kannelSMS import sendSMS

logger = logging.getLogger(__name__)

SMS_URL = os.environ.get("SMS_GATEWAY_URL", "https://my.tcell.tj/api/v1/send_sms/")
SMS_LOGIN = os.environ.get("SMS_LOGIN", "")
SMS_PASSWORD = os.environ.get("SMS_PASSWORD", "")
SMS_TIMEOUT = (3, 10)

def verify_auth_token(token):
    try:
        with connections['default'].cursor() as mycursor:
            auth_token = token
            request_id = 1222
            client_app_type = 'Web'
            client_app_version = 1
            o_subs_id = 0
            o_msisdn = ""
            o_lang_id = 0
            o_exit_location_id3 = ""
            o_responce_id3 = 0
            o_result3 = -1
            o_err_msg3 = ""
            remote_address = "127.0.0.1" #request.META.get('REMOTE_ADDR')
            args = (
                auth_token, remote_address, request_id, client_app_type, client_app_version, o_subs_id,
                o_msisdn,
                o_lang_id, o_exit_location_id3, o_responce_id3, o_result3, o_err_msg3)
            try:
                mycursor.callproc('verify_auth_token', args)
                mycursor.execute(
                    "select @_verify_auth_token_5,@_verify_auth_token_6,@_verify_auth_token_7,@_verify_auth_token_8,@_verify_auth_token_9,@_verify_auth_token_10,@_verify_auth_token_11")
                result = mycursor.fetchall()
                resp = {"exit_location_id": result[0][3], "responce_id": result[0][4], "result": result[0][5],
                        "err_msg": result[0][6]}
                lang_ref = {1: 'ru', 2: 'en', 3: 'tg'}
                user_language = lang_ref.get(result[0][2], 'ru')
                translation.activate(user_language)
                resp['err_msg'] = translation.gettext(resp['err_msg'])
                resp['err_msg'] = resp['err_msg']
                if (result[0][5] == 0):
                    resp["subs_id"] = result[0][0]
                    resp["msisdn"] = result[0][1]
                    resp["lang_id"] = result[0][2]
                return resp
            except Exception as exc:
                logger.exception("[ERROR] authentification.db.verify_auth_token (proc)")
                return {"exit_location_id": 88888, "response_id": 88888, "result": -88888,
                        "err_msg": "Error occurred while processing your request",
                        "exception_source": 'mysql', "exception_err_msg": str(exc)}

    except Exception:
        logger.exception("[ERROR] authentification.db.verify_auth_token")
        return {
            "status": "error", 
            "message":"authentification.db.verify_auth_token -> " + str(sys.exc_info()[1])
            }

# Тестовый номер для проверки приложения в сторах (SMS не отправляется).
DEV_TEST_MSISDN = os.environ.get("DEV_TEST_MSISDN", "")


def post_sent_code(phone, device_token):
    try:
        if DEV_TEST_MSISDN and phone == DEV_TEST_MSISDN:
            logger.warning("Запрос кода на тестовый номер")
            return {
                "exit_location_id": "24002",
                "response_id": 303704102,
                "result": 0,
                "err_msg": "OK",
                "txn_id": "0b3be651-1c67-11ec-9897-005056a6dd17"
                }
        with connections['default'].cursor() as mycursor:
            
            subs_id=1
            lang_id=3
            name='Тестов Тест'
            request_id=1222
            client_app_version=1
            o_sms_code=0
            o_txn_id=""
            o_exit_location_id2=""
            o_responce_id2=0
            o_result2=-1
            o_err_msg2=""
            remote_address = "127.0.0.1" #request.META.get('REMOTE_ADDR')
            args = (phone,subs_id,lang_id,name,remote_address,request_id,device_token,client_app_version, o_sms_code, o_txn_id,o_exit_location_id2, o_responce_id2, o_result2, o_err_msg2)
            mycursor.callproc('generate_sms_code', args)
            mycursor.execute("select @_generate_sms_code_8,@_generate_sms_code_9,@_generate_sms_code_10,@_generate_sms_code_11,@_generate_sms_code_12,@_generate_sms_code_13")
            result=mycursor.fetchall()
            msg = "Activation Code: " + str(result[0][0])
            logger.info("sms code generated for %s", str(phone)[-4:])
            resp={"exit_location_id":result[0][2],"response_id":result[0][3],"result":result[0][4],"err_msg":result[0][5]}
            if result[0][4]!=0:
                # процедура отказала (например, лимит кодов) - SMS не отправляем
                resp["txn_id"]=result[0][1]
                return resp

            if os.environ.get("SMS_ENABLED", "true").lower() == "true":
                payload = json.dumps({
                    "msisdn": phone[-9:],
                    "text": msg,
                    "login": SMS_LOGIN,
                    "pass": SMS_PASSWORD,
                })
                try:
                    response = requests.post(
                        SMS_URL,
                        data=payload,
                        headers={"Accept": "*/*", "Content-Type": "application/json"},
                        timeout=SMS_TIMEOUT,
                    )
                    response.raise_for_status()
                except requests.RequestException as exc:
                    logger.error("[ERROR] sms gateway: %r", exc)
                    return {"sms_unavailable": True,
                            "message": "authentification.db.post_sent_code -> sms gateway: %r" % (exc,)}

            resp = {
                        "result": 0,
                        "err_msg": "sms sent"
                        }
            resp["txn_id"]=result[0][1]
            
        return resp
    except Exception:
        return {
            "status": "error", 
            "message":"authentification.db.post_sent_code -> " + str(sys.exc_info()[1])
            }

def post_check_sent_code(request, txn_id, sms_code):
    try:
        with connections['default'].cursor() as mycursor:
            
            request_id=1222
            device_token=""
            client_app_version=1
            lang_id=1
            o_auth_token=""
            o_subs_id=0
            o_msisdn=""
            o_lang_id=1
            o_name=""
            o_exit_location_id=""
            o_responce_id=0
            o_result=0
            o_err_msg=""
            args = (txn_id,sms_code,request.META.get('REMOTE_ADDR'),request_id,device_token,client_app_version, o_auth_token,o_subs_id,o_msisdn,o_lang_id,o_name,o_exit_location_id, o_responce_id, o_result, o_err_msg)
            mycursor.callproc('verify_sms_code', args)
            mycursor.execute("select @_verify_sms_code_6,@_verify_sms_code_7,@_verify_sms_code_8,@_verify_sms_code_9,@_verify_sms_code_10,@_verify_sms_code_11,@_verify_sms_code_12,@_verify_sms_code_13,@_verify_sms_code_14")
            result=mycursor.fetchall()
            

            # при ошибках (например 22001) процедура возвращает o_msisdn = NULL
            if result[0][2]:
                mycursor.execute("Select block cnt_delivery from piza_contact_info pci where pci.phone=%s;", [result[0][2]])
                colomns_orders_id = [i[0] for i in mycursor.description]
                delivery_cnt = [dict(zip(colomns_orders_id, row)) for row in mycursor]
            else:
                delivery_cnt = []
            
            if delivery_cnt == []:
                delivery_cnt = 1

            else:
                delivery_cnt = delivery_cnt[0]['cnt_delivery']
   

            resp={"role":delivery_cnt,"msisdn":result[0][2],"lang_id":result[0][3],"name":result[0][4],"exit_location_id":result[0][5],"response_id":result[0][6],"result":result[0][7],"err_msg":result[0][8]}
            lang_id=result[0][3]
            lang_ref={1:'ru',2:'en',3:'tg'}
            user_language=lang_ref.get(lang_id,'ru')
            resp['lang'] = user_language
            translation.activate(user_language)
            if resp['err_msg']:
                resp['err_msg']=translation.gettext(resp['err_msg'])
            resp['err_msg']=resp['err_msg']
            resp["auth_token"]=result[0][0]
        return resp 


    except Exception:
        logger.exception("[ERROR] authentification.db.post_check_sent_code")
        return {
            "status": "error",
            "message": "authentification.db.post_check_sent_code -> " + str(sys.exc_info()[1])
            }

def post_logout(request):
    try:
        token = request.META.get('HTTP_AUTH_TOKEN', "")
        with connections['default'].cursor() as mycursor:
            request_id = 1222
            client_app_type = 'Web'
            client_app_version = 1
            o_subs_id = 0
            o_msisdn = ""
            o_lang_id = 0
            o_exit_location_id3 = ""
            o_responce_id3 = 0
            o_result3 = -1
            o_err_msg3 = ""

            args = (token, request.META.get('REMOTE_ADDR'), request_id, client_app_type, client_app_version,
                    o_exit_location_id3, o_responce_id3, o_result3, o_err_msg3)
            try:
                mycursor.callproc('logoff', args)
                mycursor.execute("select @_logoff_5,@_logoff_6,@_logoff_7,@_logoff_8")
                result = mycursor.fetchall()
                resp = {"exit_location_id": result[0][0], "responce_id": result[0][1], "result": result[0][2],
                        "err_msg": result[0][3]}
                return resp
            except Exception as exc:
                logger.exception("[ERROR] authentification.db.post_logout (proc)")
                return {"exit_location_id": 88886, "response_id": 88886, "result": -88886,
                        "err_msg": "Error occurred while processing your request",
                        "exception_source": 'mysql', "exception_err_msg": str(exc)}
    except Exception:
        logger.exception("[ERROR] authentification.db.post_logout")
        return {
            "status": "error", 
            "message":"authentification.db.post_logout -> " + str(sys.exc_info()[1])
            }

def send_sms(msisdn: str, text: str):
    try:
        if sendSMS(str(msisdn), text):
            resp = {
                    "result": 0,
                    "err_msg": "sms sent"
                    }
        else:
            resp = {
                    "result": -1,
                    "err_msg": "sms sent error"
                    }
        return resp
    except Exception:
        logger.exception("[ERROR] authentification.db.send_sms")
        return False