from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from piza import docs
from piza import serializers as serializer
from piza.models import (
    Products, category, orders, slide, menu_text,
    add_orders_post, add_branch_change, add_contract_post, add_pick_up,
    add_status_change, add_status_change_kitchens, order_detail, order_detail_courier,
    orders_list, orders_list_courier, orders_list_kitchens, orders_report_courier,
    profil_list, push_courier, report_list, report_order_list,
)
from piza.serializers import (
    CategoryListSerializer, DeliverySerializer, OrderDetailSerializer,
    OrderItemDetailSerializer, ProductDetailSerializer, ProductListSerializer,
    SlideListSerializer, TextMenuListSerializer,
)
from piza.utils import filterResponse


def _proc_response(result):
    """
    Единый разбор ответа слоя db/хранимой процедуры.

    err_code == 0 -> 200 с телом ответа, err_code != 0 -> 400 с кодом ошибки,
    отсутствие авторизации -> 400 с err_code -400 (как и раньше),
    внутренняя ошибка ({"status": "error"}) -> 500 без деталей наружу.
    """
    if 'err_code' in result:
        if result['err_code'] != 0:
            return Response(
                {'err_code': result['err_code'], 'err_msg': result.get('err_msg', '')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return filterResponse(result)
    if result.get('un_authorized'):
        return Response(
            {'err_code': -400, 'err_msg': "You are not authorized"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return filterResponse(result)


def _list_response(result, empty_message, ok_codes=(0, -1)):
    """Списочные методы: пустой результат - 400 с сообщением, остальное - как есть."""
    if 'err_code' in result and result['err_code'] not in ok_codes:
        return Response({"message": empty_message}, status=status.HTTP_400_BAD_REQUEST)
    return filterResponse(result)


@docs.product_create
class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductDetailSerializer


@docs.product_list
class PizaListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    # без prefetch каждый продукт тянул свои размеры отдельным запросом
    queryset = Products.objects.prefetch_related('ProductItem')


@docs.category_list
class CategoryListView(generics.ListAPIView):
    serializer_class = CategoryListSerializer
    queryset = category.objects.all()


@docs.slide_list
class SlideListView(generics.ListAPIView):
    serializer_class = SlideListSerializer
    queryset = slide.objects.all()


@docs.menu_text_list
class MenuTextListView(generics.ListAPIView):
    serializer_class = TextMenuListSerializer
    queryset = menu_text.objects.all()


@docs.product_detail
class PizaDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Products.objects.prefetch_related('ProductItem')


class PizaCategoryView(APIView):
    @docs.products_by_category
    def get(self, request, category):
        data = Products.objects.filter(category=category).prefetch_related('ProductItem')
        return Response({"products": ProductDetailSerializer(data, many=True).data})


class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderDetailSerializer


class OrderItemCreateView(generics.CreateAPIView):
    serializer_class = OrderItemDetailSerializer


class BasketList(APIView):
    @docs.basket_list
    def get(self, request):
        data = (orders.objects
                .filter(InfoDelivery__status=1)
                .select_related('InfoDelivery', 'product'))
        return Response({"BasketOrders": DeliverySerializer(data, many=True).data})


class AddContactView(APIView):
    @docs.add_contact
    def post(self, request):
        validation = serializer.AddContactSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(add_contract_post(
            request,
            name=validation.data['name'],
            adress=validation.data['adress'],
        ))


class PickUp(APIView):
    @docs.pick_up
    def post(self, request):
        validation = serializer.PickUpSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(add_pick_up(
            request,
            order_id=validation.data['order_id'],
        ))


class StatusChange(APIView):
    @docs.status_change
    def post(self, request):
        validation = serializer.StatusChangeSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(add_status_change(
            request,
            order_id=validation.data['order_id'],
            status_id=validation.data['status_id'],
        ))


class StatusChangeKitchens(APIView):
    @docs.status_change_kitchens
    def post(self, request):
        validation = serializer.StatusChangeSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(add_status_change_kitchens(
            request,
            order_id=validation.data['order_id'],
            status_id=validation.data['status_id'],
        ))


class BranchChange(APIView):
    @docs.branch_change
    def post(self, request):
        validation = serializer.BranchChangeSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(add_branch_change(
            request,
            order_id=validation.data['order_id'],
            branch_id=validation.data['branch_id'],
        ))


class OrdersList(APIView):
    @docs.orders_list
    def get(self, request):
        return _list_response(orders_list(request), "You didn't have orders")


class ReportList(APIView):
    @docs.report_list
    def post(self, request):
        validation = serializer.reportlist(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(report_list(
            request,
            period=validation.data['period'],
            branch_id=validation.data['branch_id'],
        ))


class ReporOrdertList(APIView):
    @docs.report_order_list
    def post(self, request):
        validation = serializer.reportlist(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(report_order_list(
            request,
            period=validation.data['period'],
            branch_id=validation.data['branch_id'],
        ))


class OrdersListCourier(APIView):
    @docs.orders_list_courier
    def get(self, request):
        return _list_response(orders_list_courier(request), "You didn't have orders")


class OrderDetail(APIView):
    @docs.order_detail
    def post(self, request):
        validation = serializer.orderdetail(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(order_detail(
            request,
            order_id=validation.data['order_id'],
        ))


class OrderDetailCourier(APIView):
    @docs.order_detail_courier
    def post(self, request):
        validation = serializer.orderdetail(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(order_detail_courier(
            request,
            order_id=validation.data['order_id'],
        ))


class AddOrders(APIView):
    @docs.add_orders
    def post(self, request):
        validation = serializer.addorders(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(add_orders_post(
            request,
            delivery_status=validation.data['delivery_status'],
            delivery_time=validation.data['delivery_time'],
            delivery_address=validation.data['delivery_address'],
            delivery_comment=validation.data['delivery_comment'],
            branch_id=validation.data['branch_id'],
            product=validation.data['product'],
        ))


class Profil(APIView):
    @docs.profil
    def get(self, request):
        return _list_response(
            profil_list(request),
            "Delivery information about Sun not found",
            ok_codes=(0,),
        )


class OrdersReportCourier(APIView):
    @docs.orders_report_courier
    def get(self, request):
        return _list_response(orders_report_courier(request), "You didn't have orders")


class OrdersPushCourier(APIView):
    @docs.orders_push_courier
    def post(self, request):
        validation = serializer.PickUpSerializer(data=request.data)
        validation.is_valid(raise_exception=True)
        return _proc_response(push_courier(
            request,
            order_id=validation.data['order_id'],
        ))


class OrdersListKitchens(APIView):
    @docs.orders_list_kitchens
    def get(self, request):
        return _list_response(orders_list_kitchens(request), "You didn't have orders")


def index(request):
    orders_qs = orders.objects.select_related('product')
    return render(request, 'reports/index.html', {'orders': orders_qs})
