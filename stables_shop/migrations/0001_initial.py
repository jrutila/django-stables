# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-09-12 04:31
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_fsm
import jsonfield.fields
import shop.models.customer
import stables_shop.models.activator


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0007_alter_validators_add_error_messages'),
        ('stables', '0003_auto_20151216_0808'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.SmallIntegerField(help_text='Priority for using this address')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('phone_number', models.CharField(max_length=255, verbose_name='Phone number')),
            ],
            options={
                'verbose_name': 'Billing Address',
                'verbose_name_plural': 'Billing Addresses',
            },
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('extra', jsonfield.fields.JSONField(default={}, verbose_name='Arbitrary information for this cart')),
                ('billing_address', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='stables_shop.BillingAddress')),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extra', jsonfield.fields.JSONField(default={}, verbose_name='Arbitrary information for this cart item')),
                ('quantity', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='stables_shop.Cart')),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('recognized', shop.models.customer.CustomerStateField(help_text='Designates the state the customer is recognized as.', verbose_name='Recognized as')),
                ('salutation', models.CharField(choices=[('mrs', 'Mrs.'), ('mr', 'Mr.'), ('na', '(n/a)')], max_length=5, verbose_name='Salutation')),
                ('last_access', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Last accessed')),
                ('extra', jsonfield.fields.JSONField(default={}, editable=False, verbose_name='Extra information about this customer')),
            ],
        ),
        migrations.CreateModel(
            name='DigitalShippingAddressModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='LongString',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', django_fsm.FSMField(default='new', max_length=50, protected=True, verbose_name='Status')),
                ('currency', models.CharField(editable=False, help_text='Currency in which this order was concluded', max_length=7)),
                ('_subtotal', models.DecimalField(decimal_places=2, max_digits=30, verbose_name='Subtotal')),
                ('_total', models.DecimalField(decimal_places=2, max_digits=30, verbose_name='Total')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('extra', jsonfield.fields.JSONField(default={}, help_text='Arbitrary information for this order object on the moment of purchase.', verbose_name='Extra fields')),
                ('stored_request', jsonfield.fields.JSONField(default={}, help_text='Parts of the Request objects on the moment of purchase.')),
                ('number', models.PositiveIntegerField(default=None, null=True, unique=True, verbose_name='Order Number')),
                ('shipping_address_text', models.TextField(blank=True, help_text='Shipping address at the moment of purchase.', null=True, verbose_name='Shipping Address')),
                ('billing_address_text', models.TextField(blank=True, help_text='Billing address at the moment of purchase.', null=True, verbose_name='Billing Address')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='stables_shop.Customer', verbose_name='Customer')),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(blank=True, help_text='Product name at the moment of purchase.', max_length=255, null=True, verbose_name='Product name')),
                ('product_code', models.CharField(blank=True, help_text='Product code at the moment of purchase.', max_length=255, null=True, verbose_name='Product code')),
                ('_unit_price', models.DecimalField(decimal_places=2, help_text='Products unit price at the moment of purchase.', max_digits=30, null=True, verbose_name='Unit price')),
                ('_line_total', models.DecimalField(decimal_places=2, help_text='Line total on the invoice at the moment of purchase.', max_digits=30, null=True, verbose_name='Line Total')),
                ('extra', jsonfield.fields.JSONField(default={}, help_text='Arbitrary information for this order item', verbose_name='Extra fields')),
                ('quantity', models.IntegerField(verbose_name='Ordered quantity')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='stables_shop.Order', verbose_name='Order')),
            ],
        ),
        migrations.CreateModel(
            name='PartShortUrl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash', models.CharField(default=stables_shop.models.activator.generate_hash, max_length=12, unique=True)),
                ('participation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stables.Participation', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated at')),
                ('active', models.BooleanField(default=True, help_text='Is this product publicly visible.', verbose_name='Active')),
                ('product_name', models.TextField(max_length=255)),
                ('unit_price', models.DecimalField(decimal_places=3, help_text='The whole product price excluding VAT.', max_digits=7)),
                ('slug', models.SlugField(verbose_name='Slug')),
                ('long_description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductAbsoluteDiscount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ProductActivator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(10, 'Initiated'), (20, 'Activated'), (30, 'Failed'), (40, 'Canceled')], default=10)),
            ],
        ),
        migrations.CreateModel(
            name='ProductPercentDiscount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ShippingAddress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.SmallIntegerField(help_text='Priority for using this address')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('phone_number', models.CharField(max_length=255, verbose_name='Phone number')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stables_shop.Customer')),
            ],
            options={
                'verbose_name': 'Shipping Address',
                'verbose_name_plural': 'Shipping Addresses',
            },
        ),
        migrations.CreateModel(
            name='WholePercentDiscount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='EnrollProduct',
            fields=[
                ('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='stables_shop.Product')),
                ('automatic_disable', models.BooleanField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stables.Course')),
            ],
            bases=('stables_shop.product',),
        ),
        migrations.CreateModel(
            name='EnrollProductActivator',
            fields=[
                ('productactivator_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='stables_shop.ProductActivator')),
                ('rider', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stables.RiderInfo')),
            ],
            bases=('stables_shop.productactivator',),
        ),
        migrations.CreateModel(
            name='TicketProduct',
            fields=[
                ('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='stables_shop.Product')),
                ('amount', models.PositiveIntegerField(help_text='Amount of tickets included in this product.')),
                ('duration', models.DurationField(blank=True, help_text='Relative duration of the given product. For example 30 days, 90 days. If this is empty, you must insert expire date.', null=True)),
                ('expires', models.DateField(blank=True, help_text='Absolute expiration date for the given product. For example 2014-12-31. If this is empty, you must insert duration.', null=True)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stables.TicketType')),
            ],
            bases=('stables_shop.product',),
        ),
        migrations.CreateModel(
            name='TicketProductActivator',
            fields=[
                ('productactivator_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='stables_shop.ProductActivator')),
                ('start', models.PositiveIntegerField(null=True)),
                ('end', models.PositiveIntegerField(null=True)),
                ('duration', models.DurationField(blank=True, null=True)),
                ('rider', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stables.RiderInfo')),
            ],
            bases=('stables_shop.productactivator',),
        ),
        migrations.AddField(
            model_name='productpercentdiscount',
            name='products',
            field=models.ManyToManyField(to='stables_shop.Product'),
        ),
        migrations.AddField(
            model_name='productabsolutediscount',
            name='products',
            field=models.ManyToManyField(to='stables_shop.Product'),
        ),
        migrations.AddField(
            model_name='product',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_stables_shop.product_set+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='stables_shop.Product', verbose_name='Product'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stables_shop.Product'),
        ),
        migrations.AddField(
            model_name='cart',
            name='customer',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to='stables_shop.Customer', verbose_name='Customer'),
        ),
        migrations.AddField(
            model_name='cart',
            name='shipping_address',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='stables_shop.ShippingAddress'),
        ),
        migrations.AddField(
            model_name='billingaddress',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stables_shop.Customer'),
        ),
    ]
