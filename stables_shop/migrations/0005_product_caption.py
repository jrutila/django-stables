# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-12-08 14:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stables_shop', '0004_auto_20161007_0712'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='caption',
            field=models.TextField(default='', max_length=255),
            preserve_default=False,
        ),
    ]