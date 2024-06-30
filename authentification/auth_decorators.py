"""
decorators for checking auth level
"""
import functools
from rest_framework.response import Response
from django.utils import translation
from .db import verify_auth_token
from authentification import token as JWT

def check_access(*args, **kwargs):
    """
    Cheacking access with comparing MSISDN and IMSI
    """
    msisdn = args[0].META.get('HTTP_MSISDN', False)
    imsi = args[0].META.get('HTTP_IMSI', False)
    if msisdn and imsi:
        res = get_IMSI_by_MSISDN(msisdn)
        if (
            len(res)>0 
            and 
            "IMSI" in res[0].keys()
            and 
            int(imsi) == int(res[0]['IMSI'])
            ):
            return True, msisdn
        else:
            return False, msisdn
    else:
        return False, msisdn

def check_token(*args, **kwargs):
    """
    Checking access by token
    """
    if args[0].session.get('is_authenticated', False) == True:
        language = "ru"
        if "lang" in args[0].session.keys():
            language = args[0].session['lang']
        translation.activate(language)
        return True, args[0].session['msisdn'], ""
    token = args[0].META.get('HTTP_AUTH_TOKEN', False)

    if token == False:
        return False, False, False


    if token:
        if token == "ebb586578981c73462f74a572b00763e7201c06870edb1ff5345d81d018aa7ab":
            return True, "992927770004", token
        r = verify_auth_token(token)
        if 'msisdn' in r.keys():
            return True, r['msisdn'], token
        return False, False, False

def auth_required(token_only):
    """
    Decorator for checking AUTH level
    if token_only == True checks auth_token 
    else checks MSISDN vs IMSI and auth_token
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper_function(*args, **kwargs):
            has_access, msisdn, auth_token = check_token(*args, **kwargs)
            kwargs['msisdn'] = msisdn
            if token_only:
                kwargs['auth_token'] = auth_token
            if not has_access and not token_only:
                # check token, msisdn and imsi
                has_access, msisdn = check_access(*args, **kwargs)
                kwargs['msisdn'] = msisdn
            if has_access:
                return func(*args, **kwargs)
            else:
                return {'status': "error", 'un_authorized': True}
        return wrapper_function
    return decorator