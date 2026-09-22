from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('piza', '0071_alter_orderitem_order_alter_orderitem_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='orders_report',
            fields=[],
            options={
                'verbose_name': 'Отчёт по заказам',
                'verbose_name_plural': 'Отчёт по заказам',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('piza.orders',),
        ),
    ]
