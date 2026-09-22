"""
Работа с БД приложения piza: вызовы хранимых процедур и отчётные запросы.

Все параметры передаются в драйвер как плейсхолдеры %s - подстановка значений
в текст SQL строками недопустима (SQL-инъекция).
"""
import json
import logging
import os
import sys
from datetime import date
from datetime import timedelta
from operator import itemgetter

import requests
from django.db import connections

logger = logging.getLogger(__name__)

FCM_URL = "https://fcm.googleapis.com/fcm/send"
FCM_TIMEOUT = (3, 10)
NO_TOKEN = "not token"

# Заказы кухни показываются начиная с этого номера (исторический порог).
KITCHEN_MIN_ORDER_ID = 225
# Филиалы по умолчанию, когда клиент прислал branch_id=0 ("все").
ALL_BRANCHES = (1, 2, 3)


def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _error(where):
    """Единый ответ на непредвиденную ошибку: в лог - трассировка, наружу - код."""
    logger.exception("[ERROR] %s", where)
    return {
        "status": "error",
        "message": "%s -> %s" % (where, sys.exc_info()[1]),
    }


def _branches(branch_id):
    """branch_id=0 -> все филиалы. Возвращает (плейсхолдеры, значения)."""
    try:
        branch = int(branch_id)
    except (TypeError, ValueError):
        branch = 0
    values = list(ALL_BRANCHES) if branch == 0 else [branch]
    return ", ".join(["%s"] * len(values)), values


def _period_bounds(period):
    """Границы отчётного периода: сегодня или с начала месяца по завтра."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    if period == 'month':
        return today.replace(day=1), tomorrow
    return today, tomorrow


def _merge_orders(order_rows, delivery_rows, extra_fields=(), items_by_order=None):
    """
    Сшивает суммы по заказам с данными доставки по order_id.

    Раньше это был вложенный цикл O(n*m); теперь суммы кладутся в словарь и
    обход линейный. Порядок и состав результата прежние.
    """
    sums = {row['order_id']: row['sum_order'] for row in order_rows}
    merged = []
    for row in delivery_rows:
        order_id = row['order_id']
        if order_id not in sums:
            continue
        item = {
            'order_id': order_id,
            'adress': row['adress'],
            'comment': row['comment'],
            'branch_name': row['branch_name'],
            'delivery_time': row['delivery_time'],
            'cre_date': row['cre_date'],
            'sum_order': sums[order_id],
            'status_name': row['status_name'],
        }
        for field in extra_fields:
            item[field] = row[field]
        if items_by_order is not None:
            item['product'] = items_by_order.get(order_id, [])
        merged.append(item)
    merged.sort(key=itemgetter('order_id'), reverse=True)
    return merged


def _no_orders():
    return {"err_msg": "You didn't have orders", "err_code": -1}


def _send_push(device_token, title, body):
    """Push через FCM. Ключ берётся из окружения (FCM_SERVER_KEY)."""
    if not device_token or device_token == NO_TOKEN:
        return False
    server_key = os.environ.get("FCM_SERVER_KEY", "")
    if not server_key:
        logger.warning("FCM_SERVER_KEY не задан - push не отправлен")
        return False
    try:
        response = requests.post(
            FCM_URL,
            headers={
                "Authorization": "key=" + server_key,
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "registration_ids": [device_token],
                "notification": {"title": title, "body": body},
            }),
            timeout=FCM_TIMEOUT,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("FCM push failed: %r", exc)
        return False


ORDER_SUMS_SQL = """
    select po.order_id, sum(po.paid) sum_order
    from piza_orders po
    where po.phone = %s
    group by po.order_id
"""

DELIVERY_SQL = """
    select di.phone, di.delivery_time, di.cre_date, di.adress, os.status_name,
           di.comment, di.order_id, di.courier, pb.name branch_name
    from piza_deliveryinfo di
    join piza_order_status os on os.id = di.status
    join piza_branch pb on pb.id = di.branch_id
    where di.order_id is not null
"""


def get_orders_list(msisdn):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute(ORDER_SUMS_SQL, [str(msisdn)])
            order_list = _dictfetchall(cursor)

            cursor.execute(
                DELIVERY_SQL + " and di.phone = %s order by di.cre_date desc",
                [str(msisdn)],
            )
            delivery = _dictfetchall(cursor)

        if not delivery:
            return _no_orders()
        return {
            "order_history": _merge_orders(order_list, delivery),
            "err_msg": "Order list",
            "err_code": 0,
        }
    except Exception:
        return _error("piza.db.get_orders_list")


def post_report_list(period, branch_id):
    try:
        stime, etime = _period_bounds(period)
        placeholders, branches = _branches(branch_id)

        totals_sql = """
            select count(distinct po.order_id) count_order, sum(po.paid) total_sum,
                (select sum(po.paid)
                   from piza_orders po, piza_deliveryinfo pd
                  where po.order_id = pd.order_id
                    and pd.branch_id in (%(branches)s)
                    and po.date between %%s and %%s
                    and pd.adress != '') delivery_sum,
                (select sum(po.paid)
                   from piza_orders po, piza_deliveryinfo pd
                  where po.order_id = pd.order_id
                    and pd.branch_id in (%(branches)s)
                    and po.date between %%s and %%s
                    and pd.adress = '') samovoz
            from piza_orders po, piza_deliveryinfo pd
            where po.order_id = pd.order_id
              and pd.branch_id in (%(branches)s)
              and po.date between %%s and %%s
        """ % {'branches': placeholders}
        params = (branches + [stime, etime]) * 3

        with connections['default'].cursor() as cursor:
            cursor.execute(totals_sql, params)
            report_list = _dictfetchall(cursor)
            if not report_list or report_list[0]['count_order'] == 0:
                return {"err_code": -3, "err_msg": 'Сейчас заказов нет'}

            cursor.execute("""
                select pci.name name_courier, sum(po.paid) sum
                from piza_orders po, piza_deliveryinfo pd, piza_contact_info pci
                where po.order_id = pd.order_id
                  and po.date between %s and %s
                  and pd.courier = pci.phone
                  and pd.courier != ''
                  and pd.adress != ''
                group by pci.name
            """, [stime, etime])
            report_courier = _dictfetchall(cursor)

        totals = report_list[0]
        return {
            "count_order": totals['count_order'],
            "total_sum": totals['total_sum'],
            "delivery_sum": totals['delivery_sum'],
            "samovoz": totals['samovoz'],
            "report_courier": report_courier,
            "err_code": 0,
            "err_msg": 'sucsess',
        }
    except Exception:
        return _error("piza.db.post_report_list")


def post_report_order_list(period, branch_id):
    try:
        stime, etime = _period_bounds(period)
        placeholders, branches = _branches(branch_id)

        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select po.order_id, sum(po.paid) sum_order
                from piza_orders po
                join piza_productitem pi on pi.id = po.product_value
                join piza_products pp on pp.id = po.product_id
                where po.date between %s and %s
                group by po.order_id
            """, [stime, etime])
            order_list = _dictfetchall(cursor)

            cursor.execute(
                DELIVERY_SQL + """
                  and di.cre_date between %%s and %%s
                  and di.branch_id in (%s)
                order by di.cre_date desc
                """ % placeholders,
                [stime, etime] + branches,
            )
            delivery = _dictfetchall(cursor)

        if not delivery:
            return _no_orders()
        return {
            "order_history": _merge_orders(order_list, delivery),
            "err_msg": "Order list",
            "err_code": 0,
        }
    except Exception:
        return _error("piza.db.post_report_order_list")


def post_add_orders(msisdn, delivery_status, delivery_time, delivery_address,
                    delivery_comment, branch_id, product):
    try:
        if not product:
            return {"err_code": -2, "err_msg": "Empty order"}

        with connections['default'].cursor() as cursor:
            cursor.execute("select coalesce(max(order_id), 0) + 1 as id_orders from piza_orders")
            order_id = _dictfetchall(cursor)[0]['id_orders']

            cursor.execute("""
                select ac1.device_token
                from auth_code ac1
                where ac1.stat_id = 3
                  and ac1.msisdn = %s
                  and ac1.device_token != ''
                  and ac1.cre_dt = (select max(ac2.cre_dt) from auth_code ac2
                                     where ac2.stat_id = 3 and ac2.msisdn = ac1.msisdn)
            """, [str(msisdn)])
            token_device = _dictfetchall(cursor)

            o_result = -1
            o_err_msg = ""
            resp = {"order_id": order_id, "err_code": o_result, "err_msg": o_err_msg}
            for line in product:
                args = (msisdn, line['product_id'], line['count'], line['paid'],
                        line['value'], order_id, o_result, o_err_msg)
                cursor.callproc('add_orders', args)
                cursor.execute("select @_add_orders_5,@_add_orders_6,@_add_orders_7")
                result = cursor.fetchall()
                resp = {
                    "order_id": order_id,
                    "err_code": result[0][1],
                    "err_msg": result[0][2],
                }

            args = (msisdn, delivery_status, delivery_time, delivery_address,
                    delivery_comment, order_id, branch_id, o_result, o_err_msg)
            cursor.callproc('delivery_order', args)
            cursor.execute("select @_delivery_order_5,@_delivery_order_6,@_delivery_order_7")
            cursor.fetchall()

        if token_device:
            _send_push(
                token_device[0]['device_token'],
                "Ваш заказ принят!",
                "Мы получили Ваш заказ и начали работу над ним.",
            )
        return resp
    except Exception:
        return _error("piza.db.post_add_orders")


def get_profil_list(msisdn):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select pi.id, pi.name, pi.adress
                from piza_contact_info pi
                where pi.phone = %s
                order by pi.id desc
                limit 1
            """, [str(msisdn)])
            contact_info = _dictfetchall(cursor)

        if not contact_info:
            return {"err_msg": "Profile not found", "err_code": -1}
        return {
            "phone": msisdn,
            "name": contact_info[0]['name'],
            "address": contact_info[0]['adress'],
            "err_msg": "Ok",
            "err_code": 0,
        }
    except Exception:
        return _error("piza.db.get_profil_list")


def post_order_detail(msisdn, order_id):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select po.order_id, po.phone, po.date, po.paid, po.count,
                       po.product_value volume_name, pp.id as product_id, pp.name,
                       pd.branch_id, concat('media/', pp.image) as image
                from piza_orders po
                join piza_products pp on pp.id = po.product_id
                join piza_deliveryinfo pd on pd.order_id = po.order_id
                where po.phone = %s and po.order_id = %s
                order by po.date
            """, [str(msisdn), order_id])
            order_detail = _dictfetchall(cursor)

        if not order_detail:
            return {
                "err_msg": "Order_id %s does not exist for this customer %s" % (order_id, msisdn),
                "err_code": -1,
            }
        return {"order_detail": order_detail, "err_msg": "Ok", "err_code": 0}
    except Exception:
        return _error("piza.db.post_order_detail")


def post_order_detail_courier(msisdn, order_id):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select po.order_id, po.phone, po.date, po.paid, po.count,
                       po.product_value volume_name, pp.id as product_id, pp.name,
                       pd.courier, pd.branch_id, concat('media/', pp.image) as image
                from piza_orders po
                join piza_productitem pi on pi.id = po.product_value
                join piza_products pp on pp.id = po.product_id
                join piza_deliveryinfo pd on pd.order_id = po.order_id
                where po.order_id = %s
                order by po.date
            """, [order_id])
            order_detail = _dictfetchall(cursor)

        if not order_detail:
            return {
                "err_msg": "Order_id %s does not exist for this customer %s" % (order_id, msisdn),
                "err_code": -1,
            }
        return {"order_detail": order_detail, "err_msg": "Ok", "err_code": 0}
    except Exception:
        return _error("piza.db.post_order_detail_courier")


def _call_simple_proc(proc_name, args, out_vars, where):
    """Вызов процедуры, возвращающей пару (err_code, err_msg) в OUT-переменных."""
    try:
        with connections['default'].cursor() as cursor:
            cursor.callproc(proc_name, args)
            cursor.execute("select " + ",".join(out_vars))
            result = cursor.fetchall()
            return {"err_code": result[0][0], "err_msg": result[0][1]}
    except Exception:
        return _error(where)


def post_add_contract(msisdn, name, adress):
    resp = _call_simple_proc(
        'add_contact', (msisdn, name, adress, -1, ""),
        ["@_add_contact_3", "@_add_contact_4"],
        "piza.db.post_add_contract",
    )
    if resp.get("status") == "error":
        return resp
    resp.update({"phone": msisdn, "name": name, "adress": adress})
    return resp


def post_pick_up(msisdn, order_id):
    return _call_simple_proc(
        'pick_up', (msisdn, order_id, -1, ""),
        ["@_pick_up_2", "@_pick_up_3"],
        "piza.db.post_pick_up",
    )


def post_status_change(msisdn, order_id, status_id):
    return _call_simple_proc(
        'change_status', (msisdn, order_id, status_id, -1, ""),
        ["@_change_status_3", "@_change_status_4"],
        "piza.db.post_status_change",
    )


def post_branch_change(order_id, branch_id):
    return _call_simple_proc(
        'change_branch', (order_id, branch_id, -1, ""),
        ["@_change_branch_2", "@_change_branch_3"],
        "piza.db.post_branch_change",
    )


def get_orders_list_courier(msisdn):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select po.order_id, sum(po.paid) sum_order
                from piza_orders po
                join piza_productitem pi on pi.id = po.product_value
                join piza_products pp on pp.id = po.product_id
                join piza_deliveryinfo pdi on pdi.order_id = po.order_id
                where pdi.status = 1
                  and pdi.cre_date between current_date() and now()
                group by po.order_id
            """)
            order_list = _dictfetchall(cursor)

            cursor.execute(DELIVERY_SQL + """
                  and di.status = 1
                  and di.cre_date between current_date() and now()
                order by di.cre_date desc
            """)
            delivery = _dictfetchall(cursor)

        if not delivery:
            return _no_orders()
        return {
            "order_list": _merge_orders(order_list, delivery, extra_fields=('phone', 'courier')),
            "err_msg": "Order list",
            "err_code": 0,
        }
    except Exception:
        return _error("piza.db.get_orders_list_courier")


def get_orders_report_courier(msisdn):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select sum(po.paid) sum_order, count(distinct pd.order_id) count_order
                from piza_orders po, piza_deliveryinfo pd
                where po.order_id = pd.order_id
                  and pd.courier = %s
                  and pd.status = 3
            """, [str(msisdn)])
            report_courier = _dictfetchall(cursor)

        return {
            "sum_order": report_courier[0]['sum_order'],
            "count_order": report_courier[0]['count_order'],
        }
    except Exception:
        return _error("piza.db.get_orders_report_courier")


def post_push_courier(msisdn, order_id):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select ac1.device_token
                from auth_code ac1, piza_deliveryinfo pd
                where ac1.stat_id = 3
                  and ac1.device_token != ''
                  and ac1.msisdn = pd.phone
                  and pd.order_id = %s
                  and ac1.cre_dt = (select max(ac2.cre_dt) from auth_code ac2
                                     where ac2.stat_id = 3 and ac2.msisdn = ac1.msisdn)
            """, [order_id])
            token_device = _dictfetchall(cursor)

        if not token_device:
            return {"err_code": -1, "err_msg": "Device token not found"}

        _send_push(
            token_device[0]['device_token'],
            "Доставка!",
            "Курьер на месте. Прошу принять заказ.",
        )
        return {"err_code": 0, "err_msg": "Client Alert"}
    except Exception:
        return _error("piza.db.post_push_courier")


def get_orders_list_kitchens(request):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                select po.order_id, sum(po.paid) sum_order
                from piza_orders po
                join piza_productitem pi on pi.id = po.product_value
                join piza_products pp on pp.id = po.product_id
                where po.order_id >= %s
                group by po.order_id
            """, [KITCHEN_MIN_ORDER_ID])
            order_list = _dictfetchall(cursor)

            cursor.execute(DELIVERY_SQL + " order by di.cre_date desc")
            delivery = _dictfetchall(cursor)

            # Состав заказов - одним запросом вместо запроса на каждый заказ.
            order_ids = sorted({row['order_id'] for row in order_list})
            items_by_order = {}
            if order_ids:
                placeholders = ", ".join(["%s"] * len(order_ids))
                cursor.execute("""
                    select po.order_id, po.paid, po.count, pi.volume_name,
                           pp.id as product_id, pp.name
                    from piza_orders po
                    join piza_productitem pi on pi.id = po.product_value
                    join piza_products pp on pp.id = po.product_id
                    join piza_deliveryinfo pd on pd.order_id = po.order_id
                    where po.order_id in (%s)
                    order by po.date
                """ % placeholders, order_ids)
                for row in _dictfetchall(cursor):
                    items_by_order.setdefault(row.pop('order_id'), []).append(row)

        if not delivery:
            return _no_orders()
        return {
            "order_history": _merge_orders(order_list, delivery, items_by_order=items_by_order),
            "err_msg": "Order list",
            "err_code": 0,
        }
    except Exception:
        return _error("piza.db.get_orders_list_kitchens")
