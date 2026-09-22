"""
Swagger-описания методов piza
"""
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

import piza.serializers as serializer
from authentification.docs import (
    AUTH_TOKEN_REQUIRED, SERVER_500, UNAUTHORIZED_401, VALIDATION_400,
    array, obj, prop, response,
)

TAG_CATALOG = 'Каталог'
TAG_ORDERS = 'Заказы клиента'
TAG_PROFILE = 'Профиль'
TAG_COURIER = 'Курьер'
TAG_KITCHEN = 'Кухня'
TAG_REPORTS = 'Отчёты'

STATUSES = (
    'Статусы заказа (`status_id`): 0 - Самавоз, 1 - Заказан, 2 - Карзина, '
    '3 - Доставлен, 5 - Готово, 7 - Принято.'
)

_RESULT = obj({
    'err_code': prop(int, '0 - успех, иначе код ошибки', 0),
    'err_msg': prop(str, example='Ok'),
})

_BUSINESS_400 = response(
    'Не выполнено. Возможные причины: бизнес-ошибка (`err_code` != 0), '
    'нет авторизации (`err_code = -400`, у части методов - просто строка `"Bad request"`) '
    'или неверные поля запроса',
    _RESULT,
    {'err_code': -1, 'err_msg': 'Order_id 1 does not exist for this customer 992900000000'},
)
_NO_ORDERS_400 = response(
    'Заказов нет',
    obj({'message': prop(str)}),
    {'message': "You didn't have orders"},
)

# Списки и детали заказа - общие поля позиции заказа
_ORDER_ROW = {
    'order_id': prop(int, example=101),
    'adress': prop(str, 'Адрес доставки, пустая строка - самовывоз'),
    'comment': prop(str),
    'branch_name': prop(str),
    'delivery_time': prop(str),
    'cre_date': prop(str, 'Дата-время создания заказа', '2026-09-21T14:05:00'),
    'sum_order': prop(int, 'Сумма заказа'),
    'status_name': prop(str, 'Название статуса заказа'),
}
_ORDER_ITEM = obj({
    'paid': prop(int, 'Сумма по позиции'),
    'count': prop(int, 'Количество'),
    'volume_name': prop(str, 'Размер / объём'),
    'product_id': prop(int),
    'name': prop(str, 'Название продукта'),
})

# --- Каталог -----------------------------------------------------------------------------------

product_create = method_decorator(name='post', decorator=swagger_auto_schema(
    tags=[TAG_CATALOG],
    operation_summary='Создать продукт',
))
product_list = method_decorator(name='get', decorator=swagger_auto_schema(
    tags=[TAG_CATALOG],
    operation_summary='Список продуктов',
))
category_list = method_decorator(name='get', decorator=swagger_auto_schema(
    tags=[TAG_CATALOG],
    operation_summary='Список категорий',
))
slide_list = method_decorator(name='get', decorator=swagger_auto_schema(
    tags=[TAG_CATALOG],
    operation_summary='Слайды (баннеры) главного экрана',
))
menu_text_list = method_decorator(name='get', decorator=swagger_auto_schema(
    tags=[TAG_CATALOG],
    operation_summary='Текстовые блоки меню',
))


def product_detail(cls):
    for action, summary in (
        ('get', 'Продукт по id'),
        ('put', 'Обновить продукт целиком'),
        ('patch', 'Обновить продукт частично'),
        ('delete', 'Удалить продукт'),
    ):
        cls = method_decorator(name=action, decorator=swagger_auto_schema(
            tags=[TAG_CATALOG], operation_summary=summary,
        ))(cls)
    return cls


products_by_category = swagger_auto_schema(
    tags=[TAG_CATALOG],
    operation_summary='Продукты категории',
    operation_description='`category` в URL - id категории из `/api/v1/piza/category/`.',
    responses={200: response('Продукты категории', obj({
        'products': array(openapi.Schema(type=openapi.TYPE_OBJECT)),
    }))},
)

basket_list = swagger_auto_schema(
    tags=[TAG_ORDERS],
    operation_summary='Корзина (заказы с status = 1)',
    responses={200: response('Список заказов', obj({
        'BasketOrders': array(openapi.Schema(type=openapi.TYPE_OBJECT)),
    }))},
)

# --- Заказы клиента ----------------------------------------------------------------------------

orders_list = swagger_auto_schema(
    tags=[TAG_ORDERS],
    operation_summary='История заказов клиента',
    security=AUTH_TOKEN_REQUIRED,
    responses={
        200: response('История заказов (новые сверху)', obj({
            'order_history': array(obj(_ORDER_ROW)),
            'err_msg': prop(str, example='Order list'),
            'err_code': prop(int, example=0),
        })),
        400: _NO_ORDERS_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

order_detail = swagger_auto_schema(
    tags=[TAG_ORDERS],
    operation_summary='Состав заказа клиента',
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.orderdetail,
    responses={
        200: response('Позиции заказа', obj({
            'order_detail': array(obj({
                'order_id': prop(int),
                'phone': prop(str),
                'date': prop(str),
                'paid': prop(int, 'Сумма по позиции'),
                'count': prop(int),
                'volume_name': prop(str),
                'product_id': prop(int),
                'name': prop(str),
                'branch_id': prop(int),
                'image': prop(str, 'Путь к картинке от корня сайта: media/<файл>'),
            })),
            'err_msg': prop(str, example='Ok'),
            'err_code': prop(int, example=0),
        })),
        400: _BUSINESS_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

_PRODUCT_LINE = obj({
    'product_id': prop(int, example=5),
    'count': prop(int, 'Количество', 2),
    'paid': prop(int, 'Сумма по позиции', 90),
    'value': prop(int, 'id размера / объёма (ProductItem)', 12),
}, required=['product_id', 'count', 'paid', 'value'])

add_orders = swagger_auto_schema(
    tags=[TAG_ORDERS],
    operation_summary='Оформить заказ',
    operation_description=(
        '`delivery_status` - id статуса заказа. ' + STATUSES.replace('`status_id`', '`delivery_status`') +
        ' `branch_id` - id филиала. `product[].value` - id размера / объёма продукта.'
    ),
    security=AUTH_TOKEN_REQUIRED,
    request_body=obj({
        'delivery_time': prop(str, 'Время доставки', '2026-09-21 19:30'),
        'delivery_address': prop(str, 'Адрес доставки', 'ул. Рудаки, 10'),
        'delivery_comment': prop(str, 'Комментарий к заказу'),
        'delivery_status': prop(int, example=2),
        'branch_id': prop(int, example=1),
        'product': array(_PRODUCT_LINE, 'Позиции заказа'),
    }, required=['delivery_status', 'branch_id', 'product']),
    responses={
        200: response('Заказ создан', obj({
            'order_id': prop(int, 'Номер созданного заказа'),
            'err_code': prop(int, example=0),
            'err_msg': prop(str),
        })),
        400: _BUSINESS_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

pick_up = swagger_auto_schema(
    tags=[TAG_COURIER],
    operation_summary='Курьер берёт заказ',
    operation_description=(
        'Закрепляет заказ за курьером (по `auth-token`). Заказ должен быть в статусе 1 «Заказан» '
        'и создан не более 6000 минут назад, иначе `err_code = -1`.'
    ),
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.PickUpSerializer,
    responses={200: response('Готово', _RESULT), 400: _BUSINESS_400, 401: UNAUTHORIZED_401, 500: SERVER_500},
)

# --- Профиль -----------------------------------------------------------------------------------

add_contact = swagger_auto_schema(
    tags=[TAG_PROFILE],
    operation_summary='Сохранить имя и адрес клиента',
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.AddContactSerializer,
    responses={
        200: response('Контакт сохранён', obj({
            'phone': prop(str),
            'name': prop(str),
            'adress': prop(str),
            'err_code': prop(int, example=0),
            'err_msg': prop(str),
        })),
        400: _BUSINESS_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

profil = swagger_auto_schema(
    tags=[TAG_PROFILE],
    operation_summary='Профиль клиента',
    security=AUTH_TOKEN_REQUIRED,
    responses={
        200: response('Профиль', obj({
            'phone': prop(str),
            'name': prop(str),
            'address': prop(str),
            'err_msg': prop(str, example='Ok'),
            'err_code': prop(int, example=0),
        })),
        400: response('Профиль не найден', obj({'message': prop(str)}),
                      {'message': 'Delivery information about Sun not found'}),
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

# --- Курьер ------------------------------------------------------------------------------------

orders_list_courier = swagger_auto_schema(
    tags=[TAG_COURIER],
    operation_summary='Заказы за сегодня в статусе «Заказан» (для курьера)',
    security=AUTH_TOKEN_REQUIRED,
    responses={
        200: response('Список заказов', obj({
            'order_list': array(obj({**_ORDER_ROW, 'phone': prop(str), 'courier': prop(str)})),
            'err_msg': prop(str, example='Order list'),
            'err_code': prop(int, example=0),
        })),
        400: _NO_ORDERS_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

order_detail_courier = swagger_auto_schema(
    tags=[TAG_COURIER],
    operation_summary='Состав заказа (для курьера)',
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.orderdetail,
    responses={
        200: response('Позиции заказа', obj({
            'order_detail': array(obj({
                'order_id': prop(int), 'phone': prop(str), 'date': prop(str), 'paid': prop(int),
                'count': prop(int), 'volume_name': prop(str), 'product_id': prop(int),
                'name': prop(str), 'courier': prop(str), 'branch_id': prop(int), 'image': prop(str),
            })),
            'err_msg': prop(str, example='Ok'),
            'err_code': prop(int, example=0),
        })),
        400: _BUSINESS_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

status_change = swagger_auto_schema(
    tags=[TAG_COURIER],
    operation_summary='Изменить статус заказа',
    operation_description=(
        STATUSES + ' Если заказ уже в этом статусе - `err_code = -1`, `err_msg = "Can\'t change status"`. '
        'При `status_id = 3` фиксируется время доставки.'
    ),
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.StatusChangeSerializer,
    responses={200: response('Статус изменён', _RESULT), 400: _BUSINESS_400,
               401: UNAUTHORIZED_401, 500: SERVER_500},
)

orders_report_courier = swagger_auto_schema(
    tags=[TAG_COURIER],
    operation_summary='Отчёт курьера: доставленные заказы',
    security=AUTH_TOKEN_REQUIRED,
    responses={
        200: response('Итоги по доставкам курьера', obj({
            'sum_order': prop(int, 'Сумма доставленных заказов'),
            'count_order': prop(int, 'Количество доставленных заказов'),
        })),
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

orders_push_courier = swagger_auto_schema(
    tags=[TAG_COURIER],
    operation_summary='Уведомить клиента: «Курьер на месте»',
    operation_description='Отправляет клиенту push-уведомление по заказу.',
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.PickUpSerializer,
    responses={200: response('Уведомление отправлено', _RESULT), 400: _BUSINESS_400,
               401: UNAUTHORIZED_401, 500: SERVER_500},
)

# --- Кухня -------------------------------------------------------------------------------------

orders_list_kitchens = swagger_auto_schema(
    tags=[TAG_KITCHEN],
    operation_summary='Заказы для кухни',
    operation_description='Без заголовка `auth-token`.',
    responses={
        200: response('Список заказов с составом', obj({
            'order_history': array(obj({**_ORDER_ROW, 'product': array(_ORDER_ITEM)})),
            'err_msg': prop(str, example='Order list'),
            'err_code': prop(int, example=0),
        })),
        400: _NO_ORDERS_400,
        500: SERVER_500,
    },
)

status_change_kitchens = swagger_auto_schema(
    tags=[TAG_KITCHEN],
    operation_summary='Изменить статус заказа (кухня)',
    operation_description=STATUSES + ' Без заголовка `auth-token`.',
    request_body=serializer.StatusChangeSerializer,
    responses={200: response('Статус изменён', _RESULT), 400: _BUSINESS_400, 500: SERVER_500},
)

branch_change = swagger_auto_schema(
    tags=[TAG_KITCHEN],
    operation_summary='Сменить филиал заказа',
    operation_description='Без заголовка `auth-token`.',
    request_body=serializer.BranchChangeSerializer,
    responses={200: response('Филиал изменён', _RESULT), 400: _BUSINESS_400, 500: SERVER_500},
)

# --- Отчёты ------------------------------------------------------------------------------------

_REPORT_400 = response(
    'Нет заказов (`err_code = -3`), иная бизнес-ошибка или неверные поля запроса',
    _RESULT,
    {'err_code': -3, 'err_msg': 'Сейчас заказов нет'},
)

report_list = swagger_auto_schema(
    tags=[TAG_REPORTS],
    operation_summary='Сводный отчёт по заказам',
    operation_description=(
        '`period`: `day` (по умолчанию) - за сегодня, `month` - с начала месяца. '
        '`branch_id = 0` - все филиалы.'
    ),
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.reportlist,
    responses={
        200: response('Отчёт', obj({
            'count_order': prop(int, 'Количество заказов'),
            'total_sum': prop(int, 'Общая сумма'),
            'delivery_sum': prop(int, 'Сумма доставок'),
            'samovoz': prop(int, 'Сумма самовывоза'),
            'report_courier': array(obj({
                'name_courier': prop(str),
                'sum': prop(int),
            })),
            'err_code': prop(int, example=0),
            'err_msg': prop(str),
        })),
        400: _REPORT_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)

report_order_list = swagger_auto_schema(
    tags=[TAG_REPORTS],
    operation_summary='Отчёт: список заказов за период',
    operation_description='`period`: `day` (по умолчанию) или `month`. `branch_id = 0` - все филиалы.',
    security=AUTH_TOKEN_REQUIRED,
    request_body=serializer.reportlist,
    responses={
        200: response('Список заказов (новые сверху)', obj({
            'order_history': array(obj({**_ORDER_ROW, 'phone': prop(str)})),
            'err_msg': prop(str, example='Order list'),
            'err_code': prop(int, example=0),
        })),
        400: _REPORT_400,
        401: UNAUTHORIZED_401,
        500: SERVER_500,
    },
)
