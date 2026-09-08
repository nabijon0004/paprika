import logging

import requests

logger = logging.getLogger(__name__)

# host = "http://127.0.0.1:8007"
SMS_GATEWAY_URL = "http://10.84.52.4:8007/cgi-bin/sendsms"
SMS_GATEWAY_TIMEOUT = 10


def sendSMS(msisdn, text):
    params = {
        "username": "mytcell",
        "password": "mytcell9",
        "smsc": "SMPPSim",
        "to": str(msisdn),
        "text": text,
        "from": "MyTcell",
        "coding": 2,
        "charset": "UTF-8",
    }
    try:
        resp = requests.get(SMS_GATEWAY_URL, params=params, timeout=SMS_GATEWAY_TIMEOUT)
        return resp.status_code == 202
    except requests.RequestException as e:
        logger.error("kannelSMS.sendSMS -> %s", e)
        return False