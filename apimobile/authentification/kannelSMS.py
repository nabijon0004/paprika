"""Отправка SMS через Kannel."""
import logging
import os

import requests

logger = logging.getLogger(__name__)

KANNEL_URL = os.environ.get("KANNEL_URL", "http://10.84.52.4:8007/cgi-bin/sendsms")
KANNEL_USER = os.environ.get("KANNEL_USER", "")
KANNEL_PASSWORD = os.environ.get("KANNEL_PASSWORD", "")
KANNEL_SMSC = os.environ.get("KANNEL_SMSC", "SMPPSim")
KANNEL_SENDER = os.environ.get("KANNEL_SENDER", "MyTcell")
KANNEL_TIMEOUT = (3, 10)


def sendSMS(msisdn, text):
    if not KANNEL_USER:
        logger.warning("KANNEL_USER не задан - SMS не отправлена")
        return False
    params = {
        "username": KANNEL_USER,
        "password": KANNEL_PASSWORD,
        "smsc": KANNEL_SMSC,
        "to": str(msisdn),
        "text": text,
        "from": KANNEL_SENDER,
        "coding": 2,
        "charset": "UTF-8",
    }
    try:
        # параметры передаются через params: текст экранируется драйвером
        resp = requests.get(KANNEL_URL, params=params, timeout=KANNEL_TIMEOUT)
    except requests.RequestException as exc:
        logger.error("[ERROR] kannel: %r", exc)
        return False
    return resp.status_code == 202
