import datetime
from distutils.command import upload
from tabnanny import verbose
from django.db import models
from .db import post_pizaproduct_order, get_orders_list, post_report_list, post_add_orders, get_profil_list, post_order_detail, post_add_contract, post_pick_up, get_orders_list_courier, post_order_detail_courier, post_status_change, get_orders_report_courier, post_push_courier, get_orders_list_kitchens, post_branch_change, post_report_order_list
from authentification.auth_decorators import auth_required


class category(models.Model):
    cat_name = models.CharField(verbose_name='Категория', max_length=100)
    comment = models.CharField(verbose_name='Коментарии', max_length=100, null=True)
    position = models.IntegerField(verbose_name='Позиция', blank=True, null=True)
    image = models.ImageField(upload_to = "category_icon/%Y/%m/%d", verbose_name='Значок', null=True)
    STATUS = (
            (1, 'Активна'),
            (2, 'Отключена'),
        )
    status = models.IntegerField(verbose_name='Статус', choices=STATUS)

    def __str__(self):
        return self.cat_name

    class Meta:
        verbose_name = 'Категории'
        verbose_name_plural = 'Категории'
        ordering = ['id']

class Products(models.Model):
    name = models.CharField(verbose_name='Название продукта', max_length=100, unique=True)
    position = models.IntegerField(verbose_name='Позиция', blank=True, null=True)
    CATEGORY_NMAE = (
        (1, 'Пицца'),
        (2, 'Бургер'),
        (3, 'Стрипсы'),
        (4, 'Напитки'),
        (5, 'Соус'),
        (6, 'Картофель'),
        (7, 'Десерты'),
        (8, 'Роллы'),
    )
    category = models.IntegerField(verbose_name='Категория', choices=CATEGORY_NMAE)
    #category = models.ForeignKey(category, on_delete=models.PROTECT, null=True, verbose_name='Продукт',)
    image = models.ImageField(upload_to = "photos/%Y/%m/%d", verbose_name='Фото')
    Ingredients = models.CharField(verbose_name='Ингридиенд', max_length=300)
    time_preparing = models.IntegerField(verbose_name='Время приготовления', default=0, blank=True, null=True)
    STATUS = (
        (1, 'Активна'),
        (2, 'Отключена'),
    )
    status = models.IntegerField(verbose_name='Статус', choices=STATUS)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Продукты'
        verbose_name_plural = 'Продукты'
        ordering = ['position']

class ProductItem(models.Model):
    product = models.ForeignKey(to=Products, to_field='name', related_name='ProductItem', on_delete=models.PROTECT)
    price = models.DecimalField(verbose_name='Цена', max_digits=10, decimal_places=2)
    volume_name = models.CharField(verbose_name='Объем/размер', max_length=5)

    def __str__(self):
        return  self.product_id
    def get_cost(self):
        return f'{self.product} {self.price}'

class customers(models.Model):
    name = models.CharField(verbose_name='ФИО клиент', max_length=100)
    phone = models.CharField(verbose_name='Номер телефон', max_length=12)
    device_token = models.CharField(verbose_name='Устройства', max_length=250)
    adress = models.CharField(verbose_name='Адресс', max_length=250)
    comment = models.CharField(verbose_name='Коментарии', max_length=100, null=True)
    STATUS = (
        (1, 'Активна'),
        (2, 'Отключена'),
    )
    status = models.IntegerField(verbose_name='Статус', choices=STATUS)

    class Meta:
        verbose_name = 'Клиенты'
        verbose_name_plural = 'Клиенты'
        ordering = ['-id']

class sales_report(models.Model):
    phone = models.CharField(verbose_name='Номер телефон', max_length=12)
    product = models.ForeignKey(Products, on_delete=models.PROTECT, null=True, verbose_name='Продукт',)
    product_price = models.IntegerField(verbose_name='Сумма')
    date = models.DateTimeField(verbose_name='Время продаж', max_length=15)
    delivery_address = models.CharField(verbose_name='Адресс доставки', max_length=200)
    comment = models.CharField(verbose_name='Коментарии', max_length=100, null=True)
    STATUS = (
        (1, 'Продан'),
        (2, 'Отменен'),
    )
    status = models.IntegerField(verbose_name='Статус', choices=STATUS)

    class Meta:
        verbose_name = 'Отчет по продаж'
        verbose_name_plural = 'Отчет по продаж'
        ordering = ['-date']

class TestTable(models.Model):
    id_test = models.IntegerField(blank=True, null=True)
    text = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        verbose_name = 'Тестовая таблица'
        verbose_name_plural = 'Тестовая таблица'
        managed = False
        db_table = 'test_table'

class branch(models.Model):
    name = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиал'

class slide(models.Model):
    image = models.ImageField(upload_to = "slide/%Y/%m/%d", verbose_name='Картинка')
    url = models.CharField(verbose_name='Ссылка', max_length=100, blank=True, null=True)
    priority = models.IntegerField(verbose_name='Приоритет', default=0)
    STATUS = (
        (1, 'Отркыто'),
        (2, 'Закрыто'),
    )
    status = models.IntegerField(verbose_name='Статус', choices=STATUS)

    class Meta:
        verbose_name = 'Слайд'
        verbose_name_plural = 'Слайд'

    def __str__(self):
        return 'Slide {}'.format(self.priority)

class menu_text(models.Model):
    text = models.CharField(verbose_name='Текст', max_length=100, blank=True, null=True)
    stime = models.DateTimeField(verbose_name='Дата конец', max_length=15)
    etime = models.DateTimeField(verbose_name='Дата конец', max_length=15)

    class Meta:
        verbose_name = 'Текст Меню'
        verbose_name_plural = 'Текст Меню'

    def __str__(self):
        return 'Text {}'.format(self.id)

class orders(models.Model):
    phone = models.CharField(verbose_name='Номер телефон', max_length=12)
    product = models.ForeignKey(Products, on_delete=models.PROTECT, null=True, verbose_name='Продукт')
    date = models.DateTimeField(auto_now_add=True, verbose_name='Время создание заказа', max_length=15)
    time_delivery = models.DateTimeField(verbose_name='Время доставки', max_length=15)
    adress = models.CharField(verbose_name='Адрес доставки', max_length=100, null=True)
    comment = models.CharField(verbose_name='Коментарии', max_length=100, null=True)
    paid = models.IntegerField(verbose_name='Цена')
    order_id = models.IntegerField(verbose_name='Номер заказ')

    class Meta:
        verbose_name = 'Заказы'
        verbose_name_plural = 'Заказы'
        ordering = ['-order_id']

    def __str__(self):
        return 'Заказ {}'.format(self.order_id)

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(orders, related_name='items', on_delete=models.PROTECT)
    product = models.ForeignKey(Products, related_name='order_items', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.id)

    def get_cost(self):
        return self.price * self.quantity
 
#@auth_required(token=False)
def pizaproduct_order(request, category):
    return post_pizaproduct_order(request, category)

class order_status(models.Model):
    status_name = models.CharField(verbose_name='Статус', max_length=50)

class DeliveryInfo(models.Model):
    delivery_time = models.CharField(verbose_name='Срок доставки', max_length=50, null=True)
    adress = models.CharField(verbose_name='Адрес доставки', max_length=100, null=True)
    comment = models.CharField(verbose_name='Коментарии', max_length=100, null=True)
    cre_date = models.DateTimeField(auto_now_add=True, verbose_name='Время создание заказа', max_length=15)
    phone = models.CharField(verbose_name='Телефон', max_length=12, null=True)
    courier = models.CharField(verbose_name='Курьер', max_length=12, null=True)
    STATUS = (
        (0, 'Карзина'),
        (1, 'Самовоз'),
        (2, 'В процессе'),
        (3, 'На доставке'),
        (4, 'Отказ'),
    )
    status = models.IntegerField(verbose_name='Статус', choices=STATUS)
    delivery_etime = models.DateTimeField(verbose_name='Время доставки', max_length=15)
    #order_id = models.IntegerField(verbose_name='ID заказ')
    order = models.ForeignKey(orders, related_name='InfoDelivery', on_delete=models.PROTECT)

class courier(models.Model):
    courier_phone = models.CharField(verbose_name='Телефон курьера', max_length=12, null=True)
    order_id = models.IntegerField(verbose_name='Номер заказа', null=True)
    comment = models.CharField(verbose_name='Коментарии', max_length=100, null=True)
    cre_date = models.DateTimeField(auto_now_add=True, verbose_name='Время создание заказа', max_length=15)
    STATUS = (
        (0, 'Карзина'),
        (1, 'Самовоз'),
        (2, 'В процессе'),
        (3, 'На доставке'),
        (4, 'Доставлено'),
        (5, 'Отказ'),
    )
    status = models.IntegerField(verbose_name='Статус', choices=STATUS)

class contact_info(models.Model):
    phone = models.CharField(verbose_name='Номер телефон', max_length=12)
    name = models.CharField(verbose_name='ФИО', max_length=50)
    adress = models.CharField(verbose_name='Адрес', max_length=100)
    STATUS = (
        (0, 'Открыто'),
        (1, 'Блокирован'),
        (2, 'Админ'),
        (99, 'Курьер'))
    block = models.IntegerField(verbose_name='Статус', default=0, choices=STATUS)

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = 'Контактная информация'
        verbose_name_plural = 'Контактная информация'
        ordering = ['id']

@auth_required(token_only=False)
def orders_list(request, msisdn):
    return get_orders_list(msisdn)

@auth_required(token_only=False)
def report_list(request, msisdn, period, branch_id):
    return post_report_list(period, branch_id)

@auth_required(token_only=False)
def report_order_list(request, msisdn, period, branch_id):
    return post_report_order_list(period, branch_id)

#@auth_required(token_only=False)
def orders_list_kitchens(request):
    return get_orders_list_kitchens(request)

@auth_required(token_only=False)
def add_orders_post(request, msisdn, delivery_status, delivery_time, delivery_address, delivery_comment, branch_id, product):
    return post_add_orders(msisdn, delivery_status, delivery_time, delivery_address, delivery_comment, branch_id, product)

@auth_required(token_only=False)
def profil_list(request, msisdn):
    return get_profil_list(msisdn)

@auth_required(token_only=False)
def order_detail(request, msisdn, order_id):
    return post_order_detail(msisdn, order_id)

@auth_required(token_only=False)
def order_detail_courier(request, msisdn, order_id):
    return post_order_detail_courier(msisdn, order_id)

@auth_required(token_only=False)
def add_contract_post(request, msisdn, name, adress):
    return post_add_contract(msisdn, name, adress)

@auth_required(token_only=False)
def add_pick_up(request, msisdn, order_id):
    return post_pick_up(msisdn, order_id)

@auth_required(token_only=False)
def orders_list_courier(request, msisdn):
    return get_orders_list_courier(msisdn)

@auth_required(token_only=False)
def add_status_change(request, msisdn, order_id, status_id):
    return post_status_change(msisdn, order_id, status_id)


#@auth_required(token_only=False)
def add_status_change_kitchens(request, order_id, status_id):
    return post_status_change('', order_id, status_id)

#@auth_required(token_only=False)
def add_branch_change(request, order_id, branch_id):
    return post_branch_change(order_id, branch_id)

@auth_required(token_only=False)
def orders_report_courier(request, msisdn):
    return get_orders_report_courier(msisdn)

@auth_required(token_only=False)
def push_courier(request, msisdn, order_id):
    return post_push_courier(msisdn, order_id)