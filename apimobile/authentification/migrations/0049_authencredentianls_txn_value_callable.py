"""default=generate_txn (ссылка на функцию) вместо значения, вычисленного при импорте."""
from django.db import migrations, models

import authentification.base_auth


class Migration(migrations.Migration):

    dependencies = [
        ('authentification', '0048_alter_authencredentianls_txn_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authencredentianls',
            name='txn_value',
            field=models.IntegerField(default=authentification.base_auth.generate_txn),
        ),
    ]
