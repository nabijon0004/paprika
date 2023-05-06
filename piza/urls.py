from django.contrib import admin
from django.urls import path, include
from piza.views import *
from django.conf import settings
from django.conf.urls.static import static
from . import views

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
    path('index', views.index),
    path('report-list/', ReportList.as_view()),
    path('report-order-list/', ReporOrdertList.as_view()),
]