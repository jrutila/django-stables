# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('default_discounts', '0002_auto_20160113_0803'),
        ('stables_shop', '0005_productpercentdiscount'),
    ]

    operations = [
        migrations.CreateModel(
            name='WholePercentDiscount',
            fields=[
                ('percentdiscount_ptr', models.OneToOneField(serialize=False, primary_key=True, auto_created=True, to='default_discounts.PercentDiscount', parent_link=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('default_discounts.percentdiscount',),
        ),
    ]
