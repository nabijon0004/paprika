from django.urls import path

from piza.views import (
    AddContactView, AddOrders, BasketList, BranchChange, CategoryListView,
    MenuTextListView, OrderDetail, OrderDetailCourier, OrdersList,
    OrdersListCourier, OrdersListKitchens, OrdersPushCourier, OrdersReportCourier,
    PickUp, PizaCategoryView, PizaDetailView, PizaListView, Profil,
    ProductCreateView, ReporOrdertList, ReportList, SlideListView, StatusChange,
    StatusChangeKitchens, index,
)

urlpatterns = [
    path('create-product/', ProductCreateView.as_view()),
    path('product-list/', PizaListView.as_view()),
    path('category/', CategoryListView.as_view()),
    path('detail-product/<int:pk>/', PizaDetailView.as_view()),
    path('product-ct_id/<int:category>/', PizaCategoryView.as_view()),
    path('basket-list/', BasketList.as_view()),
    path('orders-list/', OrdersList.as_view()),
    path('order-detail/', OrderDetail.as_view()),
    path('add-contact-info/', AddContactView.as_view()),
    path('pick-up/', PickUp.as_view()),
    path('add-orders/', AddOrders.as_view()),
    path('slide/', SlideListView.as_view()),
    path('menu-text/', MenuTextListView.as_view()),
    path('profil/', Profil.as_view()),
    path('orders-list-courier/', OrdersListCourier.as_view()),
    path('order-detail-courier/', OrderDetailCourier.as_view()),
    path('status-change/', StatusChange.as_view()),
    path('branch-change/', BranchChange.as_view()),
    path('status-change-kitchens/', StatusChangeKitchens.as_view()),
    path('orders-report-courier/', OrdersReportCourier.as_view()),
    path('orders-push-courier/', OrdersPushCourier.as_view()),
    path('orders-list-kitchens/', OrdersListKitchens.as_view()),
    path('index', index),
    path('report-list/', ReportList.as_view()),
    path('report-order-list/', ReporOrdertList.as_view()),
]