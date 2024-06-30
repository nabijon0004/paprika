
from heapq import merge
import sys
from django.db import connections
from django.utils import translation
from itertools import groupby
from operator import itemgetter
import requests
import json
import operator
import datetime
from datetime import date, timedelta

def post_pizaproduct_order(request, category):
    try:
        with connections['default'].cursor() as mycursor:
            
            phone='992927770004'
            time_delivery='2022-10-11 22:12:00'
            product_name='Тестов Тест'
            request_id=1222
            client_app_type='Web'
            client_app_version=1
            o_sms_code=0
            o_txn_id=""
            o_exit_location_id2=""
            o_responce_id2=0
            o_result2=-1
            o_err_msg2=""
            remote_address = "127.0.0.1" #request.META.get('REMOTE_ADDR')
            args = (phone,subs_id,lang_id,name,remote_address,request_id,client_app_type,client_app_version, o_sms_code, o_txn_id,o_exit_location_id2, o_responce_id2, o_result2, o_err_msg2)
            mycursor.callproc('generate_sms_code', args)
            mycursor.execute("select @_generate_sms_code_8,@_generate_sms_code_9,@_generate_sms_code_10,@_generate_sms_code_11,@_generate_sms_code_12,@_generate_sms_code_13")
            result=mycursor.fetchall()
            msg=translation.gettext("Код активации")+": "+str(result[0][0])
            print('phone===>>> ', phone)
            print('msg===>>> ', msg)
            # msg= "Activation Code: "+str(result[0][0])
            resp={"exit_location_id":result[0][2],"response_id":result[0][3],"result":result[0][4],"err_msg":result[0][5]}
            if result[0][4]==0:

                reqUrl = "http://my.tcell.tj/api/v1/send_sms/"
                headersList = {
                "Accept": "*/*",
                "User-Agent": "Thunder Client (https://www.thunderclient.com)",
                "Content-Type": "application/json" 
                }
                payload = json.dumps({
                                        "msisdn": phone,
                                        "text": msg,
                                        "login":"UserSms",
                                        "pass": "!Sendsms@pass"
                                        })
                response = requests.request("POST", reqUrl, data=payload,  headers=headersList)

                resp = {
                            "result": 0,
                            "err_msg": "sms sent"
                            }
                resp["txn_id"]=result[0][1]
            
        return resp
    except:
        return {
            "status": "error", 
            "message":"authentification.db.post_sent_code -> " + str(sys.exc_info()[1])
            }

def get_orders_list(msisdn):
   with connections['default'].cursor() as cursor:
    i_msisdn = msisdn
    cursor.execute("""select po.order_id, sum(po.paid) sum_order
from piza_orders po
where po.phone=""" + str(msisdn) +"""
group by order_id
order by  order_id;""")
    colomns = [i[0] for i in cursor.description]
    order_list = [dict(zip(colomns, row)) for row in cursor]
    order_list = sorted(order_list,
                    key = itemgetter('order_id'))                        

    cursor.execute("""select di.phone, di.delivery_time, di.cre_date, di.adress, os.status_name, di.comment, di.order_id, pb.name branch_name
from piza_deliveryinfo di,  piza_order_status os, piza_branch pb
where di.phone=""" + str(msisdn) +""" and di.order_id is not null and di.status=os.id and di.branch_id=pb.id order by cre_date desc;""")
    colomns_delivery = [i[0] for i in cursor.description]
    delivery = [dict(zip(colomns_delivery, row)) for row in cursor]

    merged2=[]
    for ol in order_list:
        merged2.append({
            'order_id' :ol['order_id'],
            'sum_order' :ol['sum_order'],
        })

    merged=[]
    for dl in delivery:
        merged.append({
            'order_id' :dl['order_id'],
            'branch_name' :dl['branch_name'],
            'cre_date' :dl['cre_date'],
            'adress' :dl['adress'],
            'comment' :dl['comment'],
            'delivery_time' :dl['delivery_time'],
            'phone' :dl['phone'],
            'status_name' :dl['status_name'],
        })   
    merged3=[]
    for o in merged2:
        for d in merged:
            if(o['order_id']==d['order_id']):
                merged3.append({
                    'order_id' :d['order_id'],
                    'adress' :d['adress'],
                    'comment' :d['comment'],
                    'branch_name' :d['branch_name'],
                    'delivery_time' :d['delivery_time'],
                    'cre_date' :d['cre_date'],
                    'sum_order' :o['sum_order'],
                    'status_name' :d['status_name'],
                })
    if delivery ==[]: 
        content = {
               "err_msg": "You didn't have orders",
               "err_code": -1}
        return content
    else:
        content = {
                "order_history": sorted(merged3, key=operator.itemgetter("order_id"), reverse=True),
                "err_msg": "Order list",
                "err_code": 0}
        return content

def post_report_list(period, branch_id):
    try:
        with connections['default'].cursor() as cursor:
            current_date = datetime.date.today()
            tomorrow = current_date + datetime.timedelta(days=1)
            last_day_of_prev_month = date.today().replace(day=1)

            if period == 'month':
                stime = last_day_of_prev_month
                etime = tomorrow
            else:
                stime = current_date
                etime = tomorrow

            if branch_id == 0:
                branch_id = '1,2,3'

            cursor.execute("""select count(distinct(po.order_id)) count_order, sum(po.paid) total_sum,
                            (select sum(po.paid)
                            from piza_orders po, piza_deliveryinfo pd 
                            where po.order_id=pd.order_id
                            AND pd.branch_id in (""" + str(branch_id) +""")
                            and po.date BETWEEN '""" + str(stime) +"""' AND '""" + str(etime) +"""'
                            AND pd.adress != '') delivery_sum,
                            (select sum(po.paid)
                            from piza_orders po, piza_deliveryinfo pd 
                            where po.order_id=pd.order_id
                            AND pd.branch_id in (""" + str(branch_id) +""")
                            and po.date BETWEEN '""" + str(stime) +"""' AND '""" + str(etime) +"""'
                            AND pd.adress = '') samovoz
                            from piza_orders po, piza_deliveryinfo pd 
                            where po.order_id=pd.order_id
                            AND pd.branch_id in (""" + str(branch_id) +""")
                            and po.date BETWEEN '""" + str(stime) +"""' AND '""" + str(etime) +"""' ;""")
            colomns = [i[0] for i in cursor.description]
            report_list = [dict(zip(colomns, row)) for row in cursor]
            if report_list[0]['count_order'] == 0:
                resp = {
                "err_code": -3,
                "err_msg": 'Сейчас заказов нет'}
                return resp

            cursor.execute("""select distinct(pci.name) name_courier, sum(po.paid) sum
                            from piza_orders po, piza_deliveryinfo pd, piza_contact_info pci
                            where po.order_id=pd.order_id
                            and po.date BETWEEN '""" + str(stime) +"""' AND '""" + str(etime) +"""'
                            AND pd.courier=pci.phone
                            AND pd.courier != ''
                            AND pd.adress != ''
                            group by pci.name;""")
            colomns = [i[0] for i in cursor.description]
            report_courier = [dict(zip(colomns, row)) for row in cursor]

            resp = {
                "count_order": report_list[0]['count_order'],
                "total_sum": report_list[0]['total_sum'],
                "delivery_sum": report_list[0]['delivery_sum'],
                "samovoz": report_list[0]['samovoz'],
                "report_courier": report_courier,
                "err_code": 0,
                "err_msg": 'sucsess'}
            return resp
    except:
        return {
            "status": "error", 
            "message":"db.add_contract.post_add_contract -> " + str(sys.exc_info()[1])
            }

def post_report_order_list(period, branch_id):
    try:
        with connections['default'].cursor() as cursor:
            current_date = datetime.date.today()
            tomorrow = current_date + datetime.timedelta(days=1)
            last_day_of_prev_month = date.today().replace(day=1)


            if period == 'month':
                stime = last_day_of_prev_month
                etime = tomorrow
            else:
                stime = current_date
                etime = tomorrow

            if branch_id == 0:
                branch_id = '1,2,3'
            print('stime ', stime)
            cursor.execute("""select po.order_id, sum(po.paid) sum_order
        from piza_orders po, piza_productitem pi, piza_products pp
        where  po.product_value=pi.id
        and po.product_id=pp.id
        and po.date BETWEEN '""" + str(stime) +"""' AND '""" + str(etime) +"""'
        group by order_id
        order by  order_id;""")
            colomns = [i[0] for i in cursor.description]
            order_list = [dict(zip(colomns, row)) for row in cursor]
            order_list = sorted(order_list,
                            key = itemgetter('order_id'))  

            cursor.execute("""select di.phone, di.delivery_time, di.cre_date, di.adress, os.status_name, di.comment, di.order_id, pb.name branch_name
        from piza_deliveryinfo di,  piza_order_status os, piza_branch pb
        where di.cre_date BETWEEN '""" + str(stime) +"""' AND '""" + str(etime) +"""' 
        AND di.branch_id in (""" + str(branch_id) +""")
        and di.order_id is not null and di.status=os.id and di.branch_id=pb.id order by cre_date desc;""")
            colomns_delivery = [i[0] for i in cursor.description]
            delivery = [dict(zip(colomns_delivery, row)) for row in cursor]
            merged2=[]
            for ol in order_list:
                merged2.append({
                    'order_id' :ol['order_id'],
                    'sum_order' :ol['sum_order'],
                })

            merged=[]
            for dl in delivery:
                merged.append({
                    'order_id' :dl['order_id'],
                    'branch_name' :dl['branch_name'],
                    'cre_date' :dl['cre_date'],
                    'adress' :dl['adress'],
                    'comment' :dl['comment'],
                    'delivery_time' :dl['delivery_time'],
                    'phone' :dl['phone'],
                    'status_name' :dl['status_name'],
                })   
            merged3=[]
            for o in merged2:
                for d in merged:
                    if(o['order_id']==d['order_id']):
                        merged3.append({
                            'order_id' :d['order_id'],
                            'adress' :d['adress'],
                            'comment' :d['comment'],
                            'branch_name' :d['branch_name'],
                            'delivery_time' :d['delivery_time'],
                            'cre_date' :d['cre_date'],
                            'sum_order' :o['sum_order'],
                            'status_name' :d['status_name'],
                        })
            if delivery ==[]: 
                content = {
                    "err_msg": "You didn't have orders",
                    "err_code": -1}
                return content
            else:
                content = {
                        "order_history": sorted(merged3, key=operator.itemgetter("order_id"), reverse=True),
                        "err_msg": "Order list",
                        "err_code": 0}
                return content
    except:
        return {
            "status": "error", 
            "message":"db.add_contract.post_add_contract -> " + str(sys.exc_info()[1])
            }

def post_add_orders(msisdn, delivery_status, delivery_time, delivery_address, delivery_comment, branch_id, product):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""select coalesce(max(order_id),0)+1 as id_orders from piza_orders;""")
            colomns_orders_id = [i[0] for i in cursor.description]
            orders_id = [dict(zip(colomns_orders_id, row)) for row in cursor]

            cursor.execute("""Select ac1.device_token from auth_code ac1
 where ac1.stat_id=3 and ac1.msisdn=""" + str(msisdn) +""" and ac1.device_token !=""
and ac1.cre_dt = (Select max(ac2.cre_dt) from auth_code ac2 where ac2.stat_id=3 and ac2.msisdn=ac1.msisdn);""")
            colomns_orders_id = [i[0] for i in cursor.description]
            token_device = [dict(zip(colomns_orders_id, row)) for row in cursor]
            o_result = -1
            o_err_msg = ""
            for i in range(len(product)):
                args = (
                    msisdn, product[i]['product_id'], product[i]['count'], product[i]['paid'], product[i]['value'], orders_id[0]['id_orders'], o_result, o_err_msg)
                cursor.callproc('add_orders', args)
  
                cursor.execute(
                    "select @_add_orders_5,@_add_orders_6,@_add_orders_7")
                result = cursor.fetchall()
                resp = {"order_id": orders_id[0]['id_orders'],
                    "err_code": result[0][1],
                        "err_msg": result[0][2]}

            args = (
                msisdn, delivery_status, delivery_time, delivery_address, delivery_comment, orders_id[0]['id_orders'], branch_id, o_result, o_err_msg)
            cursor.callproc('delivery_order', args)
            cursor.execute(
                "select @_delivery_order_5,@_delivery_order_6,@_delivery_order_7")
            result = cursor.fetchall()
            if token_device[0]['device_token'] !="not token":
                url = "https://fcm.googleapis.com/fcm/send"

                payload = json.dumps({
                "registration_ids": [
                    token_device[0]['device_token']
                ],
                "notification": {
                    "body": "Мы получили Ваш заказ и начали работу над ним.",
                    "title": "Ваш заказ принят!"
                }
                })
                headers = {
                'Authorization': 'key=AAAAv4PolTM:APA91bHn-kOynZHp461mj8j-SwYoMpyp3_BRGZRq_BXI4bNGzyEuunC4gkesH6X-jEplB8v45PiG3lA00O_tdxcGkaHVDcV5HyyU9ZXZxH2wH2JaLFxtP342AhT_88D4MpxqgWSytTGj',
                'Content-Type': 'application/json'
                }

                response = requests.request("POST", url, headers=headers, data=payload)
            return resp
    except:
        return {
            "status": "error", 
            "message":"db.add_orders.post_addorders -> " + str(sys.exc_info()[1])
            }

def get_profil_list(msisdn):
   with connections['default'].cursor() as cursor:
    cursor.execute("""select pi.id, pi.name, pi.adress from piza_contact_info pi where pi.phone=""" + str(msisdn) +""" and pi.id=(
select max(pi2.id) from piza_contact_info pi2 where pi2.phone=pi.phone);""")
    colomns_sum = [i[0] for i in cursor.description]
    contact_info = [dict(zip(colomns_sum, row)) for row in cursor]

    content = {
            "phone": msisdn,
            "name": contact_info[0]['name'],
            "address": contact_info[0]['adress'],
            "err_msg": "Ok",
            "err_code": 0}
    return content   

def post_order_detail(msisdn, order_id):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""select po.order_id, po.phone, po.date, po.paid, po.count, po.product_value volume_name, pp.id as product_id, pp.name, pd.branch_id, CONCAT('media/', pp.image) as image
from piza_orders po, piza_products pp, piza_deliveryinfo pd
where po.phone=""" + str(msisdn) +"""
and po.order_id=pd.order_id
and po.order_id = """ + str(order_id) +"""
and po.product_id=pp.id
order by date;""")
            colomns_orders_id = [i[0] for i in cursor.description]
            order_detail = [dict(zip(colomns_orders_id, row)) for row in cursor]
            if order_detail ==[]: 
                content = {
                    "err_msg": "Order_id "+ str(order_id) +" does not exist for this customer "+ str(msisdn),
                    "err_code": -1}
                return content
          
            content = {
            "order_detail": order_detail,
            "err_msg": "Ok",
            "err_code": 0}
            return content
    except:
        return {
            "status": "error", 
            "message":"db.add_orders.post_addorders -> " + str(sys.exc_info()[1])
            }

def post_order_detail_courier(msisdn, order_id):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("""select po.order_id, po.phone, po.date, po.paid, po.count, po.product_value volume_name, pp.id as product_id, pp.name, pd.courier, pd.branch_id, CONCAT('media/', pp.image) as image
from piza_orders po, piza_productitem pi, piza_products pp, piza_deliveryinfo pd
where po.product_value=pi.id
and po.order_id=pd.order_id
and po.order_id = """ + str(order_id) +"""
and po.product_id=pp.id
order by date;""")
            colomns_orders_id = [i[0] for i in cursor.description]
            order_detail = [dict(zip(colomns_orders_id, row)) for row in cursor]
            if order_detail ==[]: 
                content = {
                    "err_msg": "Order_id "+ str(order_id) +" does not exist for this customer "+ str(msisdn),
                    "err_code": -1}
                return content
          
            content = {
            "order_detail": order_detail,
            "err_msg": "Ok",
            "err_code": 0}
            return content
    except:
        return {
            "status": "error", 
            "message":"db.add_orders.post_addorders -> " + str(sys.exc_info()[1])
            }

def post_add_contract(msisdn, name, adress):
    try:
        with connections['default'].cursor() as cursor:
            o_result = -1
            o_err_msg = ""
            args = (
                msisdn, name, adress, o_result, o_err_msg)
            print(args)
            cursor.callproc('add_contact', args)
            cursor.execute(
                "select @_add_contact_3,@_add_contact_4;")
            result = cursor.fetchall()

            resp = {"phone":msisdn,
                "name":name,
                "adress":adress,
                "err_code": result[0][0],
                "err_msg": result[0][1]}
            return resp
    except:
        return {
            "status": "error", 
            "message":"db.add_contract.post_add_contract -> " + str(sys.exc_info()[1])
            }

def post_pick_up(msisdn, order_id):
    try:
        with connections['default'].cursor() as cursor:
            o_result = -1
            o_err_msg = ""
            args = (
                msisdn, order_id, o_result, o_err_msg)
            cursor.callproc('pick_up', args)
            cursor.execute(
                "select @_pick_up_2,@_pick_up_3;")
            result = cursor.fetchall()

            resp = {"err_code": result[0][0],
                "err_msg": result[0][1]}
            return resp
    except:
        return {
            "status": "error", 
            "message":"db.add_contract.post_add_contract -> " + str(sys.exc_info()[1])
            }

def post_status_change(msisdn, order_id, status_id):
    try:
        with connections['default'].cursor() as cursor:
            o_result = -1
            o_err_msg = ""
            args = (
                msisdn, order_id, status_id, o_result, o_err_msg)
            cursor.callproc('change_status', args)
            cursor.execute(
                "select @_change_status_3,@_change_status_4;")
            result = cursor.fetchall()

            resp = {"err_code": result[0][0],
                "err_msg": result[0][1]}
            return resp
    except:
        return {
            "status": "error", 
            "message":"db.add_contract.post_add_contract -> " + str(sys.exc_info()[1])
            }

def post_branch_change(order_id, branch_id):
    try:
        with connections['default'].cursor() as cursor:
            o_result = -1
            o_err_msg = ""
            args = (
                order_id, branch_id, o_result, o_err_msg)
            cursor.callproc('change_branch', args)
            cursor.execute(
                "select @_change_branch_2,@_change_branch_3;")
            result = cursor.fetchall()
            print(result)
            resp = {"err_code": result[0][0],
                "err_msg": result[0][1]}
            return resp
    except:
        return {
            "status": "error", 
            "message":"db.add_contract.post_add_contract -> " + str(sys.exc_info()[1])
            }


def get_orders_list_courier(msisdn):
   with connections['default'].cursor() as cursor:
    i_msisdn = msisdn
    cursor.execute("""
select po.order_id, sum(po.paid) sum_order
from piza_orders po, piza_productitem pi, piza_products pp, piza_deliveryinfo pdi
where po.order_id=pdi.order_id
and po.product_value=pi.id
and pdi.status=1
and pdi.cre_date BETWEEN CURRENT_DATE() AND NOW()
and po.product_id=pp.id
group by order_id
order by  order_id;""")
    colomns = [i[0] for i in cursor.description]
    order_list = [dict(zip(colomns, row)) for row in cursor]
    order_list = sorted(order_list,
                    key = itemgetter('order_id'))                        

    cursor.execute("""select di.phone, di.delivery_time, di.cre_date, di.adress, os.status_name, di.comment, di.order_id, pb.name branch_name, di.courier
from piza_deliveryinfo di,  piza_order_status os, piza_branch pb
where di.order_id is not null and di.status=os.id
and di.cre_date BETWEEN CURRENT_DATE() AND NOW()
and di.status=1
 and di.branch_id=pb.id order by cre_date desc;""")
    colomns_delivery = [i[0] for i in cursor.description]
    delivery = [dict(zip(colomns_delivery, row)) for row in cursor]

    merged2=[]
    for ol in order_list:
        merged2.append({
            'order_id' :ol['order_id'],
            'sum_order' :ol['sum_order'],
        })

    merged=[]
    for dl in delivery:
        merged.append({
            'order_id' :dl['order_id'],
            'branch_name' :dl['branch_name'],
            'cre_date' :dl['cre_date'],
            'adress' :dl['adress'],
            'comment' :dl['comment'],
            'delivery_time' :dl['delivery_time'],
            'phone' :dl['phone'],
            'courier' :dl['courier'],
            'status_name' :dl['status_name'],
        })   
    merged3=[]
    for o in merged2:
        for d in merged:
            if(o['order_id']==d['order_id']):
                merged3.append({
                    'order_id' :d['order_id'],
                    'adress' :d['adress'],
                    'phone' :d['phone'],
                    'courier' :d['courier'],
                    'comment' :d['comment'],
                    'branch_name' :d['branch_name'],
                    'delivery_time' :d['delivery_time'],
                    'cre_date' :d['cre_date'],
                    'sum_order' :o['sum_order'],
                    'status_name' :d['status_name'],
                })
    if delivery ==[]: 
        content = {
               "err_msg": "You didn't have orders",
               "err_code": -1}
        return content
    else:
        content = {
                "order_list": sorted(merged3, key=operator.itemgetter("order_id"), reverse=True),
                "err_msg": "Order list",
                "err_code": 0}
        return content

def get_orders_report_courier(msisdn):
   with connections['default'].cursor() as cursor:
    cursor.execute("""select sum(po.paid) sum_order, count(distinct(pd.order_id)) count_order from piza_orders po, piza_deliveryinfo pd 
where po.order_id=pd.order_id 
and pd.courier=""" + str(msisdn) +"""
and pd.status=3;""")
    colomns_report_courier = [i[0] for i in cursor.description]
    report_courier = [dict(zip(colomns_report_courier, row)) for row in cursor]

    content = {
            "sum_order": report_courier[0]['sum_order'],
            "count_order": report_courier[0]['count_order']}
    return content

def post_push_courier(msisdn, order_id):
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute(""" Select ac1.device_token from auth_code ac1, piza_deliveryinfo pd
 where ac1.stat_id=3 and ac1.device_token !=""
 and ac1.msisdn=pd.phone
 and pd.order_id=""" + str(order_id) +"""
and ac1.cre_dt = (Select max(ac2.cre_dt) from auth_code ac2 where ac2.stat_id=3 and ac2.msisdn=ac1.msisdn);""")
            colomns_orders_id = [i[0] for i in cursor.description]
            token_device = [dict(zip(colomns_orders_id, row)) for row in cursor]
            if token_device[0]['device_token'] !="not token":
                url = "https://fcm.googleapis.com/fcm/send"

                payload = json.dumps({
                "registration_ids": [
                    token_device[0]['device_token']
                ],
                "notification": {
                    "body": "Курьер на месте. Прошу принять заказ.",
                    "title": "Доставка!"
                }
                })
                headers = {
                'Authorization': 'key=AAAAv4PolTM:APA91bHn-kOynZHp461mj8j-SwYoMpyp3_BRGZRq_BXI4bNGzyEuunC4gkesH6X-jEplB8v45PiG3lA00O_tdxcGkaHVDcV5HyyU9ZXZxH2wH2JaLFxtP342AhT_88D4MpxqgWSytTGj',
                'Content-Type': 'application/json'
                }
                response = requests.request("POST", url, headers=headers, data=payload)
                resp = {"err_code": 0,
                        "err_msg": "Client Alert"}
            return resp
    except:
        return {
            "status": "error", 
            "message":"db.add_orders.post_addorders -> " + str(sys.exc_info()[1])
            }

def get_orders_list_kitchens(request):
   with connections['default'].cursor() as cursor:
    cursor.execute("""select po.order_id, sum(po.paid) sum_order
from piza_orders po, piza_productitem pi, piza_products pp
where po.product_value=pi.id
and po.order_id>=225
and po.product_id=pp.id
group by order_id
order by  order_id;""")
    colomns = [i[0] for i in cursor.description]
    order_list = [dict(zip(colomns, row)) for row in cursor]
    order_list = sorted(order_list,
                    key = itemgetter('order_id'))                        

    cursor.execute("""select di.phone, di.delivery_time, di.cre_date, di.adress, os.status_name, di.comment, di.order_id, pb.name branch_name
from piza_deliveryinfo di,  piza_order_status os, piza_branch pb
where di.order_id is not null and di.status=os.id and di.branch_id=pb.id order by cre_date desc;""")
    colomns_delivery = [i[0] for i in cursor.description]
    delivery = [dict(zip(colomns_delivery, row)) for row in cursor]
    merged2=[]
    for ol in order_list:
        merged2.append({
            'order_id' :ol['order_id'],
            'sum_order' :ol['sum_order'],
        })

    merged=[]
    for dl in delivery:
        merged.append({
            'order_id' :dl['order_id'],
            'branch_name' :dl['branch_name'],
            'cre_date' :dl['cre_date'],
            'adress' :dl['adress'],
            'comment' :dl['comment'],
            'delivery_time' :dl['delivery_time'],
            'phone' :dl['phone'],
            'status_name' :dl['status_name'],
        }) 
    merged3=[]
    for o in merged2:
        for d in merged:
            if(o['order_id']==d['order_id']):

                cursor.execute("""select po.paid, po.count, pi.volume_name, pp.id as product_id, pp.name 
                from piza_orders po, piza_productitem pi, piza_products pp, piza_deliveryinfo pd
where po.product_value=pi.id
and po.order_id=pd.order_id
and po.order_id = """ + str(d['order_id']) +"""
and po.product_id=pp.id
order by date;""")
                colomns_orders_id = [i[0] for i in cursor.description]
                order_detail = [dict(zip(colomns_orders_id, row)) for row in cursor]
                
                merged3.append({
                    'order_id' :d['order_id'],
                    'adress' :d['adress'],
                    'comment' :d['comment'],
                    'branch_name' :d['branch_name'],
                    'delivery_time' :d['delivery_time'],
                    'cre_date' :d['cre_date'],
                    'sum_order' :o['sum_order'],
                    'status_name' :d['status_name'],
                    'product' :order_detail,
                })
    if delivery ==[]: 
        content = {
               "err_msg": "You didn't have orders",
               "err_code": -1}
        return content
    else:
        content = {
                "order_history": sorted(merged3, key=operator.itemgetter("order_id"), reverse=True),
                "err_msg": "Order list",
                "err_code": 0}
        return content