# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal

from django.db import models, migrations
import shop
from shop.models import Product
import stables_shop.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0002_auto_20151007_1303'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=255)),
                ('slug', models.SlugField(verbose_name='Slug', unique=True)),
                ('long_description', models.TextField(blank=True, null=True)),
                ('active', models.BooleanField(verbose_name='Active', default=False)),
                ('date_added', models.DateTimeField(verbose_name='Date added', auto_now_add=True)),
                ('last_modified', models.DateTimeField(verbose_name='Last modified', auto_now=True)),
                ('unit_price', shop.util.fields.CurrencyField(verbose_name='Unit price', max_digits=30, default=Decimal('0.0'), decimal_places=2)),
                ('polymorphic_ctype', models.ForeignKey(editable=False, related_name='polymorphic_shop.product_set+', to='contenttypes.ContentType', null=True)),
            ],
            options={
                'verbose_name': 'Product',
                'abstract': False,
                'verbose_name_plural': 'Products',
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='Name', max_length=255)),
                ('phone_number', models.CharField(verbose_name='Phone number', max_length=255)),
                ('user_billing', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='billing_address')),
                ('user_shipping', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='shipping_address')),
            ],
            options={
                'verbose_name': 'Address',
                'verbose_name_plural': 'Addresses',
            },
        ),
        migrations.CreateModel(
            name='DigitalShippingAddressModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='EnrollProduct',
            fields=[
                ('product_ptr', models.OneToOneField(auto_created=True, parent_link=True, to=Product, primary_key=True, serialize=False)),
                ('automatic_disable', models.BooleanField()),
                ('course', models.ForeignKey(to='stables.Course')),
            ],
            bases=('stables_shop.product',),
        ),
        migrations.CreateModel(
            name='PartShortUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('hash', models.CharField(max_length=12, default=stables_shop.models.generate_hash, unique=True)),
                ('participation', models.ForeignKey(to='stables.Participation', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductActivator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('status', models.IntegerField(choices=[(10, 'Initiated'), (20, 'Activated'), (30, 'Failed'), (40, 'Canceled')], default=10)),
            ],
        ),
        migrations.CreateModel(
            name='TicketProduct',
            fields=[
                ('product_ptr', models.OneToOneField(auto_created=True, parent_link=True, to=Product, primary_key=True, serialize=False)),
                ('amount', models.PositiveIntegerField(help_text='Amount of tickets included in this product.')),
                ('duration', models.DurationField(blank=True, help_text='Relative duration of the given product. For example 30 days, 90 days. If this is empty, you must insert expire date.', null=True)),
                ('expires', models.DateField(blank=True, help_text='Absolute expiration date for the given product. For example 2014-12-31. If this is empty, you must insert duration.', null=True)),
                ('ticket', models.ForeignKey(to='stables.TicketType')),
            ],
            bases=('stables_shop.product',),
        ),
        migrations.CreateModel(
            name='EnrollProductActivator',
            fields=[
                ('productactivator_ptr', models.OneToOneField(auto_created=True, parent_link=True, to='stables_shop.ProductActivator', primary_key=True, serialize=False)),
                ('rider', models.ForeignKey(null=True, to='stables.RiderInfo', blank=True)),
            ],
            bases=('stables_shop.productactivator',),
        ),
        migrations.CreateModel(
            name='TicketProductActivator',
            fields=[
                ('productactivator_ptr', models.OneToOneField(auto_created=True, parent_link=True, to='stables_shop.ProductActivator', primary_key=True, serialize=False)),
                ('start', models.PositiveIntegerField(null=True)),
                ('end', models.PositiveIntegerField(null=True)),
                ('duration', models.DurationField(blank=True, null=True)),
                ('rider', models.ForeignKey(null=True, to='stables.RiderInfo', blank=True)),
            ],
            bases=('stables_shop.productactivator',),
        ),
        migrations.AddField(
            model_name='productactivator',
            name='order',
            field=models.ForeignKey(to='shop.Order', related_name='activators'),
        ),
        migrations.AddField(
            model_name='productactivator',
            name='order_item',
            field=models.ForeignKey(to='shop.OrderItem'),
        ),
        migrations.AddField(
            model_name='productactivator',
            name='product',
            field=models.ForeignKey(to=Product),
        ),
    ]
