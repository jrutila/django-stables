# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from decimal import Decimal
import shop.util.fields


class Migration(migrations.Migration):

    dependencies = [
        ('stables_shop', '0002_add_longstring'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unit_price',
            field=shop.util.fields.CurrencyField(default=Decimal('0.0'), verbose_name='Unit price', max_digits=30, help_text='The whole product price excluding VAT.', decimal_places=3),
        ),
    ]
