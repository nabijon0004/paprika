"""Приведение ответа слоя db к HTTP-ответу."""
import logging

from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def filterResponse(res):
    if res is None:
        logger.error("[ERROR] пустой ответ слоя db")
        return Response({"message": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if res.get('un_authorized'):
        return Response({"message": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
    if res.get('sms_unavailable'):
        logger.error("[ERROR] %s", res.get("message"))
        return Response({"message": "SMS service unavailable"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if res.get('status') == 'error':
        logger.error("[ERROR] %s", res.get("message"))
        return Response({"message": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(res, status=status.HTTP_200_OK)
