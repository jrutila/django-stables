# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('default_discounts', '0002_auto_20160113_0803'),
        ('stables_shop', '0003_decimal_places'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductAbsoluteDiscount',
            fields=[
                ('cartitemabsolutediscount_ptr', models.OneToOneField(primary_key=True, to='default_discounts.CartItemAbsoluteDiscount', auto_created=True, serialize=False, parent_link=True)),
                ('products', models.ManyToManyField(to='stables_shop.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('default_discounts.cartitemabsolutediscount',),
        ),
    ]
