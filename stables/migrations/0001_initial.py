# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stables.models.accident
import django.db.models.deletion
import stables.models.common
from django.conf import settings
import datetime
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('schedule', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Accident',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('at', models.DateTimeField()),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name': 'accident',
                'verbose_name_plural': 'accidents',
                'permissions': (('view_accidents', 'Can see detailed accident reports'),),
            },
        ),
        migrations.CreateModel(
            name='AccidentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', stables.models.accident.I18NCharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='nimi', max_length=500)),
                ('max_participants', models.IntegerField(default=7, verbose_name='maksimi osallistujamäärä')),
                ('default_participation_fee', stables.models.common.CurrencyField(default=0, verbose_name='tunnin oletushinta', max_digits=10, decimal_places=2)),
                ('api_hide', models.BooleanField(verbose_name='Hide from api', default=False)),
            ],
            options={
                'verbose_name': 'kurssi',
                'verbose_name_plural': 'tunnit',
                'permissions': (('view_participations', 'Can see detailed participations'),),
            },
        ),
        migrations.CreateModel(
            name='CourseParticipationActivator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activate_before_hours', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='CustomerInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='Enroll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.IntegerField(choices=[(6, 'Odottaa maksua'), (0, 'Osallistuu'), (3, 'Peruttu'), (4, 'Hylätty'), (1, 'Varalla')], default=6)),
                ('last_state_change_on', models.DateTimeField(default=datetime.datetime(2015, 9, 5, 10, 55, 32, 423587))),
                ('course', models.ForeignKey(to='stables.Course')),
            ],
        ),
        migrations.CreateModel(
            name='EventMetaData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('event', models.ForeignKey(to='schedule.Event')),
            ],
        ),
        migrations.CreateModel(
            name='Horse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=500)),
                ('last_usage_date', models.DateField(blank=True, verbose_name='last usage date', null=True)),
                ('day_limit', models.IntegerField(blank=True, verbose_name='day limit', null=True, help_text='How many times the horse is allowed to ride in a day. Warning will be shown if this limit is topped.')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='InstructorInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='InstructorParticipation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('event', models.ForeignKey(to='schedule.Event')),
            ],
        ),
        migrations.CreateModel(
            name='Participation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.IntegerField(choices=[(0, 'Osallistuu'), (1, 'Varalla'), (2, 'Ei osallistunut'), (3, 'Peruttu'), (4, 'Hylätty')], default=0)),
                ('note', models.TextField(blank=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('last_state_change_on', models.DateTimeField(default=datetime.datetime.now)),
                ('created_on', models.DateTimeField(default=datetime.datetime.now)),
                ('event', models.ForeignKey(to='schedule.Event')),
                ('horse', models.ForeignKey(null=True, blank=True, to='stables.Horse')),
            ],
        ),
        migrations.CreateModel(
            name='ParticipationTransactionActivator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activate_before_hours', models.IntegerField()),
                ('fee', stables.models.common.CurrencyField(max_digits=10, decimal_places=2)),
                ('participation', models.ForeignKey(to='stables.Participation')),
            ],
        ),
        migrations.CreateModel(
            name='RiderInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('customer', models.ForeignKey(to='stables.CustomerInfo')),
            ],
        ),
        migrations.CreateModel(
            name='RiderLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('includes', models.ManyToManyField(blank=True, null=True, to='stables.RiderLevel')),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('owner_id', models.PositiveIntegerField()),
                ('expires', models.DateTimeField(blank=True, verbose_name='Expires', null=True)),
                ('value', stables.models.common.CurrencyField(null=True, help_text='Sell value of one ticket. Can be used when calculating user revenue.', max_digits=10, blank=True, verbose_name='Value', decimal_places=2)),
                ('owner_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='TicketType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=32)),
                ('description', models.TextField(verbose_name='description')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('amount', stables.models.common.CurrencyField(max_digits=10, decimal_places=2)),
                ('created_on', models.DateTimeField(default=datetime.datetime.now)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('method', models.CharField(blank=True, null=True, max_length=35)),
                ('content_type', models.ForeignKey(null=True, blank=True, to='contenttypes.ContentType')),
                ('customer', models.ForeignKey(to='stables.CustomerInfo')),
            ],
            options={
                'permissions': (('can_view_saldo', 'Can see transactions and saldo'),),
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, verbose_name='phone number', max_length=128, null=True)),
                ('extra', models.TextField(blank=True, null=True)),
                ('inactive', models.BooleanField()),
                ('customer', models.OneToOneField(to='stables.CustomerInfo', on_delete=django.db.models.deletion.SET_NULL, blank=True, null=True, related_name='user')),
                ('instructor', models.OneToOneField(to='stables.InstructorInfo', blank=True, null=True, related_name='user')),
                ('rider', models.OneToOneField(to='stables.RiderInfo', on_delete=django.db.models.deletion.SET_NULL, blank=True, null=True, related_name='user')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='ticket',
            name='transaction',
            field=models.ForeignKey(null=True, blank=True, to='stables.Transaction', related_name='ticket_set'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='type',
            field=models.ForeignKey(verbose_name='Ticket type', to='stables.TicketType'),
        ),
        migrations.AddField(
            model_name='riderinfo',
            name='levels',
            field=models.ManyToManyField(blank=True, to='stables.RiderLevel', related_name='+'),
        ),
        migrations.AddField(
            model_name='participationtransactionactivator',
            name='ticket_type',
            field=models.ManyToManyField(blank=True, null=True, to='stables.TicketType'),
        ),
        migrations.AddField(
            model_name='participation',
            name='participant',
            field=models.ForeignKey(to='stables.UserProfile'),
        ),
        migrations.AddField(
            model_name='instructorparticipation',
            name='instructor',
            field=models.ForeignKey(to='stables.UserProfile'),
        ),
        migrations.AddField(
            model_name='enroll',
            name='participant',
            field=models.ForeignKey(to='stables.UserProfile'),
        ),
        migrations.AddField(
            model_name='courseparticipationactivator',
            name='enroll',
            field=models.ForeignKey(to='stables.Enroll'),
        ),
        migrations.AddField(
            model_name='course',
            name='allowed_levels',
            field=models.ManyToManyField(blank=True, verbose_name='sallitut ratsastajien tasot', to='stables.RiderLevel'),
        ),
        migrations.AddField(
            model_name='course',
            name='events',
            field=models.ManyToManyField(blank=True, null=True, to='schedule.Event'),
        ),
        migrations.AddField(
            model_name='course',
            name='ticket_type',
            field=models.ManyToManyField(blank=True, verbose_name='oletuskortti', to='stables.TicketType'),
        ),
        migrations.AddField(
            model_name='accident',
            name='horse',
            field=models.ForeignKey(to='stables.Horse'),
        ),
        migrations.AddField(
            model_name='accident',
            name='instructor',
            field=models.ForeignKey(null=True, blank=True, to='stables.InstructorInfo'),
        ),
        migrations.AddField(
            model_name='accident',
            name='rider',
            field=models.ForeignKey(to='stables.RiderInfo'),
        ),
        migrations.AddField(
            model_name='accident',
            name='type',
            field=models.ForeignKey(to='stables.AccidentType'),
        ),
        migrations.AlterUniqueTogether(
            name='participation',
            unique_together=set([('participant', 'event', 'start', 'end')]),
        ),
    ]
