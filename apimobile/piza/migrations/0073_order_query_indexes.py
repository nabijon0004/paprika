"""Индексы под запросы списков заказов и отчётов (фильтры по phone/date/order_id)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('piza', '0072_orders_report'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='orders',
            index=models.Index(fields=['order_id'], name='piza_orders_order_id_idx'),
        ),
        migrations.AddIndex(
            model_name='orders',
            index=models.Index(fields=['phone'], name='piza_orders_phone_idx'),
        ),
        migrations.AddIndex(
            model_name='orders',
            index=models.Index(fields=['date'], name='piza_orders_date_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryinfo',
            index=models.Index(fields=['phone'], name='piza_delivery_phone_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryinfo',
            index=models.Index(fields=['courier'], name='piza_delivery_courier_idx'),
        ),
        migrations.AddIndex(
            model_name='deliveryinfo',
            index=models.Index(fields=['cre_date'], name='piza_delivery_cre_date_idx'),
        ),
        migrations.AddIndex(
            model_name='contact_info',
            index=models.Index(fields=['phone'], name='piza_contact_phone_idx'),
        ),
    ]
