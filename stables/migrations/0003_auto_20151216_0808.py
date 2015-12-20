# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0002_auto_20151007_1303'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enroll',
            name='last_state_change_on',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
