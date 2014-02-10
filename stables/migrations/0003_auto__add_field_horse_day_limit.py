# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Horse.day_limit'
        db.add_column(u'stables_horse', 'day_limit',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Horse.day_limit'
        db.delete_column(u'stables_horse', 'day_limit')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'schedule.calendar': {
            'Meta': {'object_name': 'Calendar'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200'})
        },
        'schedule.event': {
            'Meta': {'object_name': 'Event'},
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Calendar']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'end_recurring_period': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rule': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Rule']", 'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'schedule.rule': {
            'Meta': {'object_name': 'Rule'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'params': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'stables.accident': {
            'Meta': {'object_name': 'Accident'},
            'at': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'horse': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Horse']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.InstructorInfo']", 'null': 'True', 'blank': 'True'}),
            'rider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.RiderInfo']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.AccidentType']"})
        },
        'stables.accidenttype': {
            'Meta': {'object_name': 'AccidentType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('stables.models.accident.I18NCharField', [], {'max_length': '1000'})
        },
        'stables.course': {
            'Meta': {'object_name': 'Course'},
            'allowed_levels': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['stables.RiderLevel']", 'symmetrical': 'False', 'blank': 'True'}),
            'course_fee': ('stables.models.financial.CurrencyField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'default_participation_fee': ('stables.models.financial.CurrencyField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'events': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['schedule.Event']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_participants': ('django.db.models.fields.IntegerField', [], {'default': '7'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'ticket_type': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['stables.TicketType']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'stables.courseparticipationactivator': {
            'Meta': {'object_name': 'CourseParticipationActivator'},
            'activate_before_hours': ('django.db.models.fields.IntegerField', [], {}),
            'enroll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Enroll']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'stables.coursetransactionactivator': {
            'Meta': {'object_name': 'CourseTransactionActivator'},
            'enroll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Enroll']"}),
            'fee': ('stables.models.financial.CurrencyField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'stables.customerinfo': {
            'Meta': {'object_name': 'CustomerInfo'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'stables.enroll': {
            'Meta': {'object_name': 'Enroll'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Course']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_state_change_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 5, 0, 0)'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.UserProfile']"}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '6'})
        },
        'stables.eventmetadata': {
            'Meta': {'object_name': 'EventMetaData'},
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
        },
        'stables.horse': {
            'Meta': {'object_name': 'Horse'},
            'day_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_usage_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'stables.instructorinfo': {
            'Meta': {'object_name': 'InstructorInfo'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'stables.instructorparticipation': {
            'Meta': {'object_name': 'InstructorParticipation'},
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Event']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.UserProfile']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
        },
        'stables.participation': {
            'Meta': {'unique_together': "(('participant', 'event', 'start', 'end'),)", 'object_name': 'Participation'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Event']"}),
            'horse': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Horse']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_state_change_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.UserProfile']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stables.participationtransactionactivator': {
            'Meta': {'object_name': 'ParticipationTransactionActivator'},
            'activate_before_hours': ('django.db.models.fields.IntegerField', [], {}),
            'fee': ('stables.models.financial.CurrencyField', [], {'max_digits': '10', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Participation']"}),
            'ticket_type': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['stables.TicketType']", 'null': 'True', 'blank': 'True'})
        },
        'stables.riderinfo': {
            'Meta': {'object_name': 'RiderInfo'},
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.CustomerInfo']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'levels': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'+'", 'blank': 'True', 'to': "orm['stables.RiderLevel']"})
        },
        'stables.riderlevel': {
            'Meta': {'object_name': 'RiderLevel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'includes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['stables.RiderLevel']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'stables.ticket': {
            'Meta': {'object_name': 'Ticket'},
            'expires': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 5, 0, 0)', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'transaction': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ticket_set'", 'null': 'True', 'to': "orm['stables.Transaction']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.TicketType']"}),
            'value': ('stables.models.financial.CurrencyField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'})
        },
        'stables.tickettype': {
            'Meta': {'object_name': 'TicketType'},
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'stables.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'amount': ('stables.models.financial.CurrencyField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.CustomerInfo']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'stables.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'customer': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'user'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['stables.CustomerInfo']", 'blank': 'True', 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructor': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'user'", 'unique': 'True', 'null': 'True', 'to': "orm['stables.InstructorInfo']"}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'rider': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'user'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['stables.RiderInfo']", 'blank': 'True', 'unique': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['stables']