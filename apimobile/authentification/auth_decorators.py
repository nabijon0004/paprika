"""
Декораторы проверки уровня авторизации.
"""
import functools
import logging
import os

from django.utils import translation

from .db import verify_auth_token

logger = logging.getLogger(__name__)

# Отладочный токен для тестового номера. Задаётся только в dev-окружении
# (переменные DEV_AUTH_TOKEN и DEV_AUTH_MSISDN); в проде обе пустые.
DEV_AUTH_TOKEN = os.environ.get("DEV_AUTH_TOKEN", "")
DEV_AUTH_MSISDN = os.environ.get("DEV_AUTH_MSISDN", "")


def check_token(request, *args, **kwargs):
    """Проверка доступа по auth-token или по активной сессии."""
    if request.session.get('is_authenticated', False):
        translation.activate(request.session.get('lang', 'ru'))
        return True, request.session['msisdn'], ""

    token = request.META.get('HTTP_AUTH_TOKEN', "")
    if not token:
        return False, False, False

    if DEV_AUTH_TOKEN and DEV_AUTH_MSISDN and token == DEV_AUTH_TOKEN:
        logger.warning("Использован отладочный auth-token")
        return True, DEV_AUTH_MSISDN, token

    result = verify_auth_token(token)
    if 'msisdn' in result:
        return True, result['msisdn'], token
    return False, False, False


def auth_required(token_only):
    """
    Проверяет auth-token и подставляет msisdn в kwargs вызываемой функции.
    При token_only=True в kwargs также кладётся сам токен.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper_function(request, *args, **kwargs):
            has_access, msisdn, auth_token = check_token(request, *args, **kwargs)
            kwargs['msisdn'] = msisdn
            if token_only:
                # именно auth_token: с дефисом это не имя параметра,
                # и обёрнутые функции падали с TypeError
                kwargs['auth_token'] = auth_token
            if has_access:
                return func(request, *args, **kwargs)
            return {'status': "error", 'un_authorized': True}
        return wrapper_function
    return decorator
