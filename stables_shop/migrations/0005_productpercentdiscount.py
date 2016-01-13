# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('default_discounts', '0002_auto_20160113_0803'),
        ('stables_shop', '0004_productabsolutediscount'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductPercentDiscount',
            fields=[
                ('cartitempercentdiscount_ptr', models.OneToOneField(auto_created=True, serialize=False, primary_key=True, parent_link=True, to='default_discounts.CartItemPercentDiscount')),
                ('products', models.ManyToManyField(to='stables_shop.Product')),
            ],
            options={
                'abstract': False,
            },
            bases=('default_discounts.cartitempercentdiscount',),
        ),
    ]
