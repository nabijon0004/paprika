from django.contrib import admin

# Register your models here.


from .models import Products, customers, category, sales_report, TestTable, orders, OrderItem, ProductItem, contact_info, DeliveryInfo, branch, slide, menu_text

class ProductItemAdmin(admin.TabularInline):
    model = ProductItem
    raw_id_fields = ['product']

class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'position','status')
    search_fields = ('name', 'category')
    inlines = [ProductItemAdmin]

    list_filter = ['category']


admin.site.register(Products, ProductsAdmin)

class CategorysAdmin(admin.ModelAdmin):
    list_display = ('cat_name', 'position', 'comment', 'status')
    search_fields = ('cat_name', 'status')

admin.site.register(category, CategorysAdmin)

class Sales_reportsAdmin(admin.ModelAdmin):
    list_display = ('phone', 'product_id', 'product_price', 'date' , 'delivery_address', 'status')
    search_fields = ('phone', 'delivery_address')

admin.site.register(sales_report, Sales_reportsAdmin)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

class DeliveryAdmin(admin.TabularInline):
    model = DeliveryInfo
    raw_id_fields = ['order']


class OrdersAdmin(admin.ModelAdmin):
    list_display = ('phone', 'date', 'order_id')
    search_fields = ('phone', 'delivery_address')
    list_filter = ['date']
    #inlines = [DeliveryAdmin]

admin.site.register(orders, OrdersAdmin)

class ContacInfoAdmin(admin.ModelAdmin):
    list_display = ('phone', 'name', 'adress', 'block')
    search_fields = ('phone', 'name')

admin.site.register(contact_info, ContacInfoAdmin)


class BranchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')

admin.site.register(branch, BranchAdmin)

class SlideAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'url', 'status', 'priority')
    search_fields = ('id', 'image')

admin.site.register(slide, SlideAdmin)

class TextMenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'stime', 'etime')
    search_fields = ('id', 'text')

admin.site.register(menu_text, TextMenuAdmin)