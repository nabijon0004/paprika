#from apimobile.piza.models import orders
from itertools import count
from rest_framework import serializers
from piza.models import Products, category, orders, OrderItem, ProductItem, contact_info, slide, menu_text, courier

class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = '__all__'

class DeliverySerializer(serializers.ModelSerializer):
    InfoDelivery = ProductItemSerializer(many=True)
    class Meta:
        model = orders
        depth =2
        fields = ('id', 'InfoDelivery','time_delivery', 'adress', 'comment', 'date', 'phone')

class BasketSerializer(serializers.ModelSerializer):
    class Meta:
        model = orders
        fields = '__all__'

class ProductDetailSerializer(serializers.ModelSerializer):
    ProductItem = ProductItemSerializer(many=True)
    class Meta:
        model = Products
        depth =2
        fields = ('id', 'name', 'ProductItem', 'Ingredients', 'category', 'position', 'time_preparing', 'image', 'status')

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        depth =1
        fields = ('id', 'name', 'ProductItem', 'Ingredients', 'category', 'position', 'image', 'status')

class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = category
        fields = ('id', 'cat_name', 'comment', 'position', 'image', 'status')

class SlideListSerializer(serializers.ModelSerializer):
    class Meta:
        model = slide
        fields = ('id', 'image', 'url', 'status', 'priority')

class TextMenuListSerializer(serializers.ModelSerializer):
    class Meta:
        model = menu_text
        fields = ('id', 'text')

class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = orders
        fields = '__all__'

class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class AddContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = contact_info
        fields = ('name', 'adress')

class PickUpSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

class StatusChangeSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    status_id = serializers.IntegerField()

class BranchChangeSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    branch_id = serializers.IntegerField()

class PizaOrder(serializers.Serializer):
    phone = serializers.CharField(required=True)
    time_delivery = serializers.DateField(required=True)
    product_name = serializers.CharField()
    product_value = serializers.CharField(required=True)
    adress = serializers.CharField(required=True)
    comment = serializers.CharField(required=True)

class addorders(serializers.Serializer):
    delivery_time = serializers.CharField(default='')
    delivery_address = serializers.CharField(default='')
    delivery_comment = serializers.CharField(default='')
    delivery_status = serializers.IntegerField()
    product = serializers.JSONField()
    branch_id = serializers.IntegerField()

class orderdetail(serializers.Serializer):
    order_id = serializers.IntegerField()


class reportlist(serializers.Serializer):
    period = serializers.CharField(default='day')
    branch_id = serializers.IntegerField()