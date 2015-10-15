# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shop.util.fields
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('stables_shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LongString',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='product',
            options={},
        ),
        migrations.AlterField(
            model_name='product',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', related_name='polymorphic_stables_shop.product_set+', editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='unit_price',
            field=shop.util.fields.CurrencyField(default=Decimal('0.0'), decimal_places=2, verbose_name='Unit price', help_text='The whole product price excluding VAT.', max_digits=30),
        ),
    ]
