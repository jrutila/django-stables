# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('stables', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enroll',
            name='last_state_change_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 7, 13, 2, 11, 462703)),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='inactive',
            field=models.BooleanField(default=False),
        ),
    ]
