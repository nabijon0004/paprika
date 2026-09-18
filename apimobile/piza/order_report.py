"""
Отчёт по заказам (история заказов) для админки.

Заказ - это группа строк piza_orders с одинаковым order_id (одна строка на позицию).
Данные о доставке (курьер, статус, адрес, филиал) лежат в piza_deliveryinfo и
связаны по order_id, как и во всех остальных отчётах приложения (см. db.py).
"""
import datetime
import re
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.shortcuts import render
from django.utils import timezone

PER_PAGE = 50
REPORT_TZ = ZoneInfo('Asia/Dushanbe')  # даты в БД - UTC, в отчёте - время Душанбе
NO_COURIER = '-'

# ключ сортировки -> колонка во внешнем запросе
SORT_COLUMNS = {
    'order_id': 't.order_id',
    'date': 't.order_date',
    'client': 't.client_name',
    'phone': 't.phone',
    'courier': 't.courier_name',
    'total': 't.total',
    'status': 't.status_name',
}
DEFAULT_SORT = 'date'
DEFAULT_DIR = 'desc'

COLUMNS = (
    ('order_id', 'Заказ №'),
    ('date', 'Дата (Душанбе)'),
    ('client', 'Клиент'),
    ('phone', 'Телефон'),
    ('courier', 'Курьер'),
    ('status', 'Статус'),
    ('total', 'Сумма'),
)

# Один заказ = одна строка. Из piza_deliveryinfo берётся последняя запись по заказу
# (у части заказов их две), у старых заказов доставки нет вовсе - поэтому LEFT JOIN.
BASE_SQL = """
SELECT
    ord.order_id,
    ord.order_date,
    ord.phone,
    ord.total,
    ord.items,
    NULLIF(dlv.courier, '') AS courier,
    dlv.status,
    dlv.adress,
    dlv.delivery_time,
    dlv.comment,
    (SELECT ci.name FROM piza_contact_info ci WHERE ci.phone = ord.phone
        ORDER BY ci.id LIMIT 1) AS client_name,
    (SELECT ci.name FROM piza_contact_info ci WHERE ci.phone = dlv.courier
        ORDER BY ci.id LIMIT 1) AS courier_name,
    (SELECT os.status_name FROM piza_order_status os WHERE os.id = dlv.status
        LIMIT 1) AS status_name,
    (SELECT b.name FROM piza_branch b WHERE b.id = dlv.branch_id
        LIMIT 1) AS branch_name
FROM (
    SELECT po.order_id,
           MIN(po.date) AS order_date,
           MIN(po.phone) AS phone,
           SUM(po.paid) AS total,
           GROUP_CONCAT(CONCAT(COALESCE(p.name, '-'), ' - ', po.paid)
                        ORDER BY po.id SEPARATOR '||') AS items
    FROM piza_orders po
    LEFT JOIN piza_products p ON p.id = po.product_id
    GROUP BY po.order_id
) ord
LEFT JOIN (
    SELECT x.* FROM (
        SELECT pd.*, ROW_NUMBER() OVER (
            PARTITION BY pd.order_id ORDER BY pd.cre_date DESC) AS rn
        FROM piza_deliveryinfo pd
    ) x WHERE x.rn = 1
) dlv ON dlv.order_id = ord.order_id
"""


def _parse_date(value):
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _to_utc_naive(day):
    """Начало дня по Душанбе -> naive UTC (так даты лежат в БД)."""
    aware = datetime.datetime.combine(day, datetime.time.min, tzinfo=REPORT_TZ)
    return aware.astimezone(datetime.timezone.utc).replace(tzinfo=None)


def _local(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(REPORT_TZ)


def _fetch(cursor, sql, params=()):
    cursor.execute(sql, params)
    names = [c[0] for c in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def order_report(request, admin_context, has_permission):
    if not has_permission:
        raise PermissionDenied

    get = request.GET
    q = get.get('q', '').strip()
    courier = get.get('courier', '').strip()
    client = get.get('client', '').strip()
    date_from = _parse_date(get.get('date_from'))
    date_to = _parse_date(get.get('date_to'))
    sort = get.get('sort') if get.get('sort') in SORT_COLUMNS else DEFAULT_SORT
    direction = get.get('dir') if get.get('dir') in ('asc', 'desc') else DEFAULT_DIR
    try:
        page = max(int(get.get('page', 1)), 1)
    except ValueError:
        page = 1

    where, params = [], []
    digits = re.sub(r'\D', '', q)
    if digits:
        where.append('t.phone LIKE %s')
        params.append('%' + digits + '%')
    if courier == NO_COURIER:
        where.append('t.courier IS NULL')
    elif courier:
        where.append('t.courier = %s')
        params.append(courier)
    if client:
        where.append('t.phone = %s')
        params.append(client)
    if date_from:
        where.append('t.order_date >= %s')
        params.append(_to_utc_naive(date_from))
    if date_to:
        where.append('t.order_date < %s')
        params.append(_to_utc_naive(date_to + datetime.timedelta(days=1)))
    where_sql = (' WHERE ' + ' AND '.join(where)) if where else ''

    order_sql = ' ORDER BY %s %s, t.order_id DESC' % (
        SORT_COLUMNS[sort], direction.upper())  # только значения из белого списка

    with connection.cursor() as cursor:
        summary = _fetch(
            cursor,
            'SELECT COUNT(*) AS cnt, COALESCE(SUM(t.total), 0) AS total FROM (%s) t%s'
            % (BASE_SQL, where_sql), params)[0]
        pages = max((summary['cnt'] + PER_PAGE - 1) // PER_PAGE, 1)
        page = min(page, pages)
        rows = _fetch(
            cursor,
            'SELECT t.* FROM (%s) t%s%s LIMIT %d OFFSET %d'
            % (BASE_SQL, where_sql, order_sql, PER_PAGE, (page - 1) * PER_PAGE),
            params)
        couriers = _fetch(
            cursor,
            """SELECT c.courier AS phone,
                      (SELECT ci.name FROM piza_contact_info ci
                        WHERE ci.phone = c.courier ORDER BY ci.id LIMIT 1) AS name
               FROM (SELECT DISTINCT courier FROM piza_deliveryinfo
                      WHERE courier IS NOT NULL AND courier != '') c
               ORDER BY name, phone""")
        clients = _fetch(
            cursor,
            """SELECT c.phone,
                      (SELECT ci.name FROM piza_contact_info ci
                        WHERE ci.phone = c.phone ORDER BY ci.id LIMIT 1) AS name
               FROM (SELECT DISTINCT phone FROM piza_orders) c
               ORDER BY name IS NULL, name, phone""")

    for row in rows:
        row['order_date'] = _local(row['order_date'])
        row['items'] = row['items'].split('||') if row['items'] else []

    filters = {
        'q': q, 'courier': courier, 'client': client,
        'date_from': date_from.isoformat() if date_from else '',
        'date_to': date_to.isoformat() if date_to else '',
    }
    active = {k: v for k, v in filters.items() if v}

    def url(**extra):
        query = dict(active, **{'sort': sort, 'dir': direction})
        query.update(extra)
        return '?' + urlencode(query)

    headers = []
    for key, label in COLUMNS:
        is_current = key == sort
        next_dir = 'asc' if (is_current and direction == 'desc') else 'desc'
        if key != 'total' and key != 'date' and not is_current:
            next_dir = 'asc'
        headers.append({
            'label': label,
            'url': url(sort=key, dir=next_dir),
            'arrow': ('▲' if direction == 'asc' else '▼') if is_current else '',
        })

    context = dict(
        admin_context,
        title='Отчёт по заказам',
        rows=rows,
        headers=headers,
        summary=summary,
        filters=filters,
        has_filters=bool(active),
        couriers=couriers,
        clients=clients,
        no_courier=NO_COURIER,
        sort=sort,
        direction=direction,
        page=page,
        pages=pages,
        prev_url=url(page=page - 1) if page > 1 else '',
        next_url=url(page=page + 1) if page < pages else '',
        per_page=PER_PAGE,
    )
    # шаблоны сами переводят даты в TIME_ZONE проекта, поэтому на время рендера меняем пояс
    with timezone.override(REPORT_TZ):
        return render(request, 'admin/piza/orders/order_report.html', context)
