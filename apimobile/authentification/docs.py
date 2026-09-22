"""
Swagger-описания для методов авторизации и общие хелперы для piza.docs
"""
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from authentification import serializer

TAG_AUTH = 'Авторизация (SMS)'

# Метод требует заголовок auth-token (см. SWAGGER_SETTINGS в settings.py)
AUTH_TOKEN_REQUIRED = [{'AuthToken': []}]

_TYPES = {
    str: openapi.TYPE_STRING,
    int: openapi.TYPE_INTEGER,
    float: openapi.TYPE_NUMBER,
    bool: openapi.TYPE_BOOLEAN,
}


def prop(kind, description=None, example=None):
    """Схема простого поля: prop(str, 'описание', 'пример')"""
    return openapi.Schema(type=_TYPES[kind], description=description, example=example)


def obj(properties, description=None, required=None):
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        description=description,
        properties=properties,
        required=required,
    )


def array(items, description=None):
    return openapi.Schema(type=openapi.TYPE_ARRAY, items=items, description=description)


def response(description, schema=None, example=None):
    return openapi.Response(
        description,
        schema=schema,
        examples={'application/json': example} if example is not None else None,
    )


MESSAGE = obj({'message': prop(str)})

VALIDATION_400 = response(
    'Ошибка валидации запроса: ключ - имя поля, значение - список ошибок',
    example={'phone': ['Обязательное поле.']},
)
UNAUTHORIZED_401 = response(
    'Не авторизован: заголовок auth-token не передан или недействителен',
    MESSAGE,
    {'message': 'Not authorized'},
)
SERVER_500 = response('Внутренняя ошибка сервера', MESSAGE, {'message': 'Server error'})

send_code = swagger_auto_schema(
    tags=[TAG_AUTH],
    operation_summary='Отправить SMS-код на номер телефона',
    operation_description=(
        'Первый шаг входа. Генерирует SMS-код и отправляет его на телефон. '
        'В ответе приходит `txn_id`, его нужно передать вместе с кодом из SMS '
        'в `/auth/check-sent-code/`. Время жизни `txn_id` - 15 минут.\n\n'
        'Если процедура отказала (например, превышен лимит кодов), ответ тоже `200`, '
        'но `result` не равен 0, а в `exit_location_id` и `err_msg` - причина.'
    ),
    request_body=serializer.SendCode,
    responses={
        200: response(
            'SMS отправлено',
            obj({
                'result': prop(int, '0 - успех', 0),
                'err_msg': prop(str, example='sms sent'),
                'txn_id': prop(str, 'Идентификатор транзакции для check-sent-code',
                               '2eedf47d-b4ba-11f1-ae20-4296620f54d1'),
                'exit_location_id': prop(str, 'Только при отказе процедуры'),
            }),
            {'result': 0, 'err_msg': 'sms sent',
             'txn_id': '2eedf47d-b4ba-11f1-ae20-4296620f54d1'},
        ),
        400: VALIDATION_400,
        500: SERVER_500,
        503: response('SMS-шлюз недоступен', MESSAGE, {'message': 'SMS service unavailable'}),
    },
)

check_sent_code = swagger_auto_schema(
    tags=[TAG_AUTH],
    operation_summary='Проверить SMS-код и получить auth_token',
    operation_description=(
        'Второй шаг входа. Успех - `200` и `exit_location_id = 22008`; '
        '`auth_token` из ответа передаётся заголовком `auth-token` во все защищённые методы.\n\n'
        '**Любой другой результат - `401`.** Причину смотрите в `exit_location_id` / `err_msg`:\n\n'
        '| exit_location_id | err_msg |\n'
        '|---|---|\n'
        '| 22001 | Токен некорректный |\n'
        '| 22002, 22004 | Токен уже используется |\n'
        '| 22003, 22005 | Срок действия txn_id уже истек. Время его жизни составляет 15 минут. |\n'
        '| 22006 | Слишком много попыток подтверждения через SMS-код |\n'
        '| 22007 | Неверный SMS-код |\n'
        '| 22008 | OK (успех, `200`) |'
    ),
    request_body=serializer.CheckSentCode,
    responses={
        200: response(
            'Код подтверждён',
            obj({
                'role': prop(int, 'Поле block из контактов: 0 - открыто, 1 - заблокирован '
                                  '(также значение по умолчанию, если записи нет), 2 - админ, 99 - курьер'),
                'msisdn': prop(str, example='992900000000'),
                'lang_id': prop(int, '1 - ru, 2 - en, 3 - tg', 1),
                'name': prop(str),
                'exit_location_id': prop(str, example='22008'),
                'response_id': prop(int, example=1),
                'result': prop(int, '0 - успех', 0),
                'err_msg': prop(str, example='OK'),
                'lang': prop(str, example='ru'),
                'auth_token': prop(str, 'Токен для заголовка auth-token'),
            }),
            {
                'role': 1, 'msisdn': '992900000000', 'lang_id': 1, 'name': 'Фамилия Имя Отчество',
                'exit_location_id': '22008', 'response_id': 1, 'result': 0, 'err_msg': 'OK',
                'lang': 'ru', 'auth_token': '<auth_token>',
            },
        ),
        400: VALIDATION_400,
        401: response(
            'Код не подтверждён (см. таблицу кодов выше)',
            obj({
                'exit_location_id': prop(str, example='22007'),
                'result': prop(int, example=-1),
                'err_msg': prop(str, example='Неверный SMS-код'),
                'msisdn': prop(str), 'auth_token': prop(str),
            }),
            {
                'role': 1, 'msisdn': None, 'lang_id': None, 'name': None, 'exit_location_id': '22007',
                'response_id': 0, 'result': -1, 'err_msg': 'Неверный SMS-код', 'lang': 'ru',
                'auth_token': None,
            },
        ),
    },
)

_LOGOUT_RESPONSES = {
    200: response('Сессия завершена'),
    401: UNAUTHORIZED_401,
    500: SERVER_500,
}

logoff_get = swagger_auto_schema(
    tags=[TAG_AUTH],
    operation_summary='Выйти из аккаунта',
    operation_description='Завершает сессию по заголовку `auth-token`.',
    security=AUTH_TOKEN_REQUIRED,
    responses=_LOGOUT_RESPONSES,
)
logoff_post = swagger_auto_schema(
    tags=[TAG_AUTH],
    operation_summary='Выйти из аккаунта (POST)',
    operation_description='То же, что GET `/auth/logoff/`. Тело запроса не нужно.',
    security=AUTH_TOKEN_REQUIRED,
    responses=_LOGOUT_RESPONSES,
)

# Метод работает, но в документацию не попадает
hidden = swagger_auto_schema(auto_schema=None)
