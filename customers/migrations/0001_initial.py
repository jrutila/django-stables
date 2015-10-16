# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tenant_schemas.postgresql_backend.base


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('domain_url', models.CharField(unique=True, max_length=128)),
                ('schema_name', models.CharField(unique=True, max_length=63, validators=[tenant_schemas.postgresql_backend.base._check_schema_name])),
                ('name', models.CharField(max_length=100)),
                ('created_on', models.DateField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
