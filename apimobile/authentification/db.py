"""
All connection with db
"""
import logging

import requests
from django.db import connections, DatabaseError
from django.utils import translation

from authentification.kannelSMS import sendSMS

logger = logging.getLogger(__name__)

_LANG_REF = {1: 'ru', 2: 'en', 3: 'tg'}
_DB_ERROR_MESSAGE = "Error occurred while processing your request"


def _call_proc(cursor, proc_name, args, out_count):
    """
    Call a stored procedure and return a row with its OUT parameters.

    MySQL exposes OUT parameters of the last callproc as session
    variables named @_<proc_name>_<index>.
    """
    cursor.callproc(proc_name, args)
    out_vars = ",".join(
        f"@_{proc_name}_{i}" for i in range(len(args) - out_count, len(args))
    )
    cursor.execute(f"SELECT {out_vars}")
    return cursor.fetchone()


def _db_error_response(marker, exc):
    """Build a response dict for MySQL errors (marker: 88888 / 88886)."""
    err_code = exc.args[0] if len(exc.args) > 0 else marker
    err_msg = exc.args[1] if len(exc.args) > 1 else str(exc)
    return {
        "exit_location_id": marker,
        "response_id": marker,
        "result": -marker,
        "err_msg": _DB_ERROR_MESSAGE,
        "exception_source": "mysql",
        "exception_err_code": err_code,
        "exception_err_msg": err_msg,
    }


def _error_response(func_name, exc):
    logger.error("authentification.db.%s -> %s", func_name, exc)
    return {
        "status": "error",
        "message": f"authentification.db.{func_name} -> {exc}",
    }


def _send_activation_sms(phone, sms_code):
    """Send activation code via the Tcell SMS gateway."""
    msg = "Activation Code: " + str(sms_code)
    logger.debug("phone===>>> %s", phone)
    logger.debug("msg===>>> %s", msg)
    req_url = "https://my.tcell.tj/api/v1/send_sms/"
    headers = {
        "Accept": "*/*",
        "User-Agent": "Thunder Client (https://www.thunderclient.com)",
        "Content-Type": "application/json",
    }
    payload = {
        "msisdn": phone[-9:],
        "text": msg,
        "login": "UserSms",
        "pass": "!Sendsms@pass",
    }
    response = requests.post(req_url, json=payload, headers=headers, timeout=10)
    logger.debug("sms gateway resp %s", response)


def verify_auth_token(token):
    try:
        with connections['default'].cursor() as mycursor:
            args = (
                token, "127.0.0.1", 1222, 'Web', 1, 0,
                "", 0, "", 0, -1, "",
            )
            try:
                result = _call_proc(mycursor, 'verify_auth_token', args, 7)
                resp = {
                    "exit_location_id": result[3],
                    "responce_id": result[4],
                    "result": result[5],
                    "err_msg": result[6],
                }
                translation.activate(_LANG_REF.get(result[2], 'ru'))
                resp['err_msg'] = translation.gettext(resp['err_msg'])
                if result[5] == 0:
                    resp["subs_id"] = result[0]
                    resp["msisdn"] = result[1]
                    resp["lang_id"] = result[2]
                return resp
            except DatabaseError as e:
                return _db_error_response(88888, e)
    except Exception as e:
        return _error_response('verify_auth_token', e)

def post_sent_code(phone, device_token):
    try:
        if phone == "992927720598":
            return {
                "exit_location_id": "24002",
                "response_id": 303704102,
                "result": 0,
                "err_msg": "OK",
                "txn_id": "0b3be651-1c67-11ec-9897-005056a6dd17"
                }
        with connections['default'].cursor() as mycursor:
            args = (
                phone, 1, 3, 'Тестов Тест', "127.0.0.1", 1222,
                device_token, 1, 0, "", "", 0, -1, "",
            )
            result = _call_proc(mycursor, 'generate_sms_code', args, 6)
            if result[4] == 0:
                _send_activation_sms(phone, result[0])
            return {
                "result": 0,
                "err_msg": "sms sent",
                "txn_id": result[1],
            }
    except Exception as e:
        return _error_response('post_sent_code', e)

def post_check_sent_code(request, txn_id, sms_code):
    try:
        with connections['default'].cursor() as mycursor:
            args = (
                txn_id, sms_code, request.META.get('REMOTE_ADDR'), 1222, "", 1,
                "", 0, "", 1, "", "", 0, 0, "",
            )
            result = _call_proc(mycursor, 'verify_sms_code', args, 9)

            mycursor.execute(
                "SELECT block cnt_delivery FROM piza_contact_info pci WHERE pci.phone = %s",
                (result[2],),
            )
            row = mycursor.fetchone()
            delivery_cnt = row[0] if row else 1

            lang_id = result[3]
            user_language = _LANG_REF.get(lang_id, 'ru')
            translation.activate(user_language)
            resp = {
                "role": delivery_cnt,
                "msisdn": result[2],
                "lang_id": lang_id,
                "name": result[4],
                "exit_location_id": result[5],
                "response_id": result[6],
                "result": result[7],
                "err_msg": translation.gettext(result[8]),
                "lang": user_language,
                "auth_token": result[0],
            }
            logger.debug("resp %s", resp)
            return resp
    except Exception as e:
        return _error_response('post_check_sent_code', e)

def post_logout(request):
    try:
        token = request.META.get('HTTP_AUTH_TOKEN', "")
        with connections['default'].cursor() as mycursor:
            args = (
                token, request.META.get('REMOTE_ADDR'), 1222, 'Web', 1,
                "", 0, -1, "",
            )
            try:
                result = _call_proc(mycursor, 'logoff', args, 4)
                return {
                    "exit_location_id": result[0],
                    "responce_id": result[1],
                    "result": result[2],
                    "err_msg": result[3],
                }
            except DatabaseError as e:
                return _db_error_response(88886, e)
    except Exception as e:
        return _error_response('post_logout', e)

def send_sms(msisdn: str, text: str):
    try:
        if sendSMS(str(msisdn), text):
            return {
                "result": 0,
                "err_msg": "sms sent"
                }
        return {
            "result": -1,
            "err_msg": "sms sent error"
            }
    except Exception as e:
        logger.error("authentification.db.send_sms -> %s", e)
        return False