from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import generics, status
from piza.serializers import ProductDetailSerializer, ProductListSerializer, ProductCategorySerializer, CategoryListSerializer, OrderDetailSerializer, OrderItemDetailSerializer, ProductItemSerializer, AddContactSerializer, PizaOrder, DeliverySerializer, SlideListSerializer, TextMenuListSerializer
from piza.models import Products, category, ProductItem, pizaproduct_order, orders, add_orders_post, profil_list, orders_list, report_list, report_order_list, order_detail, slide, menu_text, add_contract_post, add_pick_up, orders_list_courier, order_detail_courier, add_status_change, orders_report_courier, push_courier, orders_list_kitchens, add_branch_change, add_status_change_kitchens
from rest_framework.views import APIView
from rest_framework.response import Response
from piza.utils import filterResponse
import piza.serializers as serializer
from http.server import HTTPServer, SimpleHTTPRequestHandler, test
import json
from authentification.auth_decorators import auth_required

class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductDetailSerializer

class PizaListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    queryset = Products.objects.all()


class CategoryListView(generics.ListAPIView):
    serializer_class = CategoryListSerializer
    queryset = category.objects.all()

class SlideListView(generics.ListAPIView):
    serializer_class = SlideListSerializer
    queryset = slide.objects.all()

class MenuTextListView(generics.ListAPIView):
    serializer_class = TextMenuListSerializer
    queryset = menu_text.objects.all()

class PizaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Products.objects.all()

class PizaCategoryView(APIView):
    def get(self, request, category):
        data = Products.objects.filter(category=category).all()
        productinfo = ProductDetailSerializer(data=data, many=True)
        productinfo.is_valid()
        return Response({"products": productinfo.data})

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderDetailSerializer

class OrderItemCreateView(generics.CreateAPIView):
    serializer_class = OrderItemDetailSerializer

class BasketList(APIView):
    def get(self, request):
        data = orders.objects.filter(status=1).all()
        BasketInfo = DeliverySerializer(data=data, many=True)
        BasketInfo.is_valid()
        return Response({"BasketOrders": BasketInfo.data})

class PizaOrders(APIView):
    def post(self, request):
        validation = serializer.PizaOrder(data=request.data)
        if validation.is_valid(raise_exception=True):
            return filtering(
                pizaproduct_order(
                    request, 
                    phone=validation.data['phone']
                    )
            )
        else:
            return Response({"message":"Bad request"}, status=status.HTTP_400_BAD_REQUEST)


class AddContactView(generics.CreateAPIView):
    serializer_class = AddContactSerializer

class AddContactView(APIView):        
    def post(self, request):
        print('request ', request.data)
        validation = serializer.AddContactSerializer(data=request.data)
        if validation.is_valid(raise_exception=True):
            r=add_contract_post(
                    request, 
                    name = validation.data['name'],
                    adress = validation.data['adress']
                )
            print('r', r)
            if 'err_code' in r.keys():
                if r['err_code']!=0:
                    content = {
                        'err_code': r['err_code'],
                        'err_msg': 'err_msg',
                        }
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return filterResponse(
                        r
                    )
            elif  r['un_authorized']==True:
                content = {
                        'err_code': -400,
                        'err_msg': "You are not authorized",
                        }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class PickUp(APIView):        
    def post(self, request):
        validation = serializer.PickUpSerializer(data=request.data)
        if validation.is_valid(raise_exception=True):
            r=add_pick_up(
                    request, 
                    order_id = validation.data['order_id']
                )
            if 'err_code' in r.keys():
                if r['err_code']!=0:
                    content = {
                        'err_code': r['err_code'],
                        'err_msg': r['err_msg'],
                        }
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return filterResponse(
                        r
                    )
            elif  r['un_authorized']==True:
                content = {
                        'err_code': -400,
                        'err_msg': "You are not authorized",
                        }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class StatusChange(APIView):        
    def post(self, request):
        validation = serializer.StatusChangeSerializer(data=request.data)
        if validation.is_valid(raise_exception=True):
            r=add_status_change(
                    request, 
                    order_id = validation.data['order_id'],
                    status_id = validation.data['status_id']
                )
            if 'err_code' in r.keys():
                if r['err_code']!=0:
                    content = {
                        'err_code': r['err_code'],
                        'err_msg': r['err_msg'],
                        }
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return filterResponse(
                        r
                    )
            elif  r['un_authorized']==True:
                content = {
                        'err_code': -400,
                        'err_msg': "You are not authorized",
                        }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class StatusChangeKitchens(APIView):        
    def post(self, request):
        validation = serializer.StatusChangeSerializer(data=request.data)
        if validation.is_valid(raise_exception=True):
            r=add_status_change_kitchens(
                    request, 
                    order_id = validation.data['order_id'],
                    status_id = validation.data['status_id']
                )
            if 'err_code' in r.keys():
                if r['err_code']!=0:
                    content = {
                        'err_code': r['err_code'],
                        'err_msg': r['err_msg'],
                        }
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return filterResponse(
                        r
                    )
            elif  r['un_authorized']==True:
                content = {
                        'err_code': -400,
                        'err_msg': "You are not authorized",
                        }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class BranchChange(APIView):        
    def post(self, request):
        validation = serializer.BranchChangeSerializer(data=request.data)
        if validation.is_valid(raise_exception=True):
            r=add_branch_change(
                    request, 
                    order_id = validation.data['order_id'],
                    branch_id = validation.data['branch_id']
                )
            if 'err_code' in r.keys():
                if r['err_code']!=0:
                    content = {
                        'err_code': r['err_code'],
                        'err_msg': r['err_msg'],
                        }
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return filterResponse(
                        r
                    )
            elif  r['un_authorized']==True:
                content = {
                        'err_code': -400,
                        'err_msg': "You are not authorized",
                        }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class OrdersList(APIView):
    def get(self, request):
        resp=orders_list(request)
        if 'err_code' in resp.keys():
            if resp['err_code'] not in (0, -1):
                content = {
                    'result': -1,
                    'err_msg': 'Err resp test',
                }
                return Response({"message":"You didn't have orders"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return filterResponse(
                    resp
                )
        else:
            return filterResponse(resp)

class ReportList(APIView):
    def post(self, request):
            validation = serializer.reportlist(data=request.data)
            if validation.is_valid(raise_exception=True):
                r = report_list(
                        request, 
                        period=validation.data['period'],
                        branch_id=validation.data['branch_id']
                        )
                if 'err_code' in r.keys():
                    if r['err_code']!=0:
                        content = {
                            'err_code': r['err_code'],
                            'err_msg': r['err_msg'],
                            }
                        return Response(content, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return filterResponse(
                            r
                        )
                else:                
                    return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class ReporOrdertList(APIView):
    def post(self, request):
            validation = serializer.reportlist(data=request.data)
            if validation.is_valid(raise_exception=True):
                r = report_order_list(
                        request, 
                        period=validation.data['period'],
                        branch_id=validation.data['branch_id']
                        )
                if 'err_code' in r.keys():
                    if r['err_code']!=0:
                        content = {
                            'err_code': r['err_code'],
                            'err_msg': r['err_msg'],
                            }
                        return Response(content, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return filterResponse(
                            r
                        )
                else:                
                    return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class OrdersListCourier(APIView):
    def get(self, request):
        resp=orders_list_courier(request)
        if 'err_code' in resp.keys():
            if resp['err_code'] not in (0, -1):
                content = {
                    'result': -1,
                    'err_msg': 'Err resp test',
                }
                return Response({"message":"You didn't have orders"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return filterResponse(
                    resp
                )
        else:
            return filterResponse(resp)

class OrderDetail(APIView):
    def post(self, request):
            validation = serializer.orderdetail(data=request.data)
            if validation.is_valid(raise_exception=True):
                r = order_detail(
                        request, 
                        order_id=validation.data['order_id']
                        )
                if 'err_code' in r.keys():
                    if r['err_code']!=0:
                        content = {
                            'err_code': r['err_code'],
                            'err_msg': r['err_msg'],
                            }
                        return Response(content, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return filterResponse(
                            r
                        )
                else:                
                    return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class OrderDetailCourier(APIView):
    def post(self, request):
            validation = serializer.orderdetail(data=request.data)
            if validation.is_valid(raise_exception=True):
                r = order_detail_courier(
                        request, 
                        order_id=validation.data['order_id']
                        )
                if 'err_code' in r.keys():
                    if r['err_code']!=0:
                        content = {
                            'err_code': r['err_code'],
                            'err_msg': r['err_msg'],
                            }
                        return Response(content, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return filterResponse(
                            r
                        )
                else:                
                    return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class AddOrders(APIView):        
    def post(self, request):
        print('request ', request.data)
        validation = serializer.addorders(data=request.data)
        if validation.is_valid(raise_exception=True):
            r=add_orders_post(
                    request, 
                    delivery_status = validation.data['delivery_status'],
                    delivery_time = validation.data['delivery_time'],
                    delivery_address = validation.data['delivery_address'],
                    delivery_comment = validation.data['delivery_comment'],
                    branch_id = validation.data['branch_id'],
                    product = validation.data['product']
                )
            if 'err_code' in r.keys():
                if r['err_code']!=0:
                    content = {
                        'err_code': r['err_code'],
                        'err_msg': r['err_msg'],
                        }
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return filterResponse(
                        r
                    )
            elif  r['un_authorized']==True:
                content = {
                        'err_code': -400,
                        'err_msg': "You are not authorized",
                        }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                print('===>>> ', r)
                return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)

class Profil(APIView):
    def get(self, request):
        resp=profil_list(request)
        if 'err_code' in resp.keys():
            if resp['err_code'] !=0:
                content = {
                    'result': -1,
                    'err_msg': 'Err resp test',
                }
                return Response({"message":"Delivery information about Sun not found"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return filterResponse(
                    resp
                )
        else:
            return filterResponse(resp)

class OrdersReportCourier(APIView):
    def get(self, request):
        resp=orders_report_courier(request)
        if 'err_code' in resp.keys():
            if resp['err_code'] not in (0, -1):
                content = {
                    'result': -1,
                    'err_msg': 'Err resp test',
                }
                return Response({"message":"You didn't have orders"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return filterResponse(
                    resp
                )
        else:
            return filterResponse(resp)

class OrdersPushCourier(APIView):        
    def post(self, request):
        validation = serializer.PickUpSerializer(data=request.data)
        if validation.is_valid(raise_exception=True):
            r=push_courier(
                    request, 
                    order_id = validation.data['order_id']
                )
            if 'err_code' in r.keys():
                if r['err_code']!=0:
                    content = {
                        'err_code': r['err_code'],
                        'err_msg': r['err_msg'],
                        }
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return filterResponse(
                        r
                    )
            elif  r['un_authorized']==True:
                content = {
                        'err_code': -400,
                        'err_msg': "You are not authorized",
                        }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Bad request', status=status.HTTP_400_BAD_REQUEST)


class OrdersListKitchens(APIView):
    def get(self, request):
        resp=orders_list_kitchens(request)
        if 'err_code' in resp.keys():
            if resp['err_code'] not in (0, -1):
                content = {
                    'result': -1,
                    'err_msg': 'Err resp test',
                }
                return Response({"message":"You didn't have orders"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return filterResponse(
                    resp
                )
        else:
            return filterResponse(resp)
    

def index(request):
    orders_list = orders.objects.all()
    # res = '<h1>Список заказов</h1>'
    # for order in orders_list:
    #     print(order)
    #     res +=f'<div><h3>{ order.order_id }</h3><div>{ order.date }</div></div><hr>'
    # return HttpResponse(res)
    return render(request, 'reports/index.html', {'orders': orders_list})


from django.shortcuts import render, get_object_or_404
from .models import orders, Products

def order_detail(request, order_id):
    order = get_object_or_404(orders, order_id=order_id)
    context = {
        'order': order,
        'products': order.product.values()
    }
    return render(request, 'order_detail.html', context)