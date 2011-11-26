# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Rider'
        db.delete_table('stables_rider')

        # Deleting model 'Owner'
        db.delete_table('stables_owner')

        # Deleting model 'Customer'
        db.delete_table('stables_customer')

        # Adding model 'CustomerInfo'
        db.create_table('stables_customerinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('stables', ['CustomerInfo'])

        # Adding model 'RiderInfo'
        db.create_table('stables_riderinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('level', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('stables', ['RiderInfo'])

        # Changing field 'Enroll.rider'
        db.alter_column('stables_enroll', 'rider_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.UserProfile']))

        # Deleting field 'Horse.owner'
        db.delete_column('stables_horse', 'owner_id')

        # Changing field 'UserProfile.customer'
        db.alter_column('stables_userprofile', 'customer_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.CustomerInfo'], unique=True, null=True))

        # Changing field 'UserProfile.rider'
        db.alter_column('stables_userprofile', 'rider_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.RiderInfo'], unique=True, null=True))

        # Changing field 'Course.creator'
        db.alter_column('stables_course', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.UserProfile'], null=True))

        # Changing field 'Participation.participant'
        db.alter_column('stables_participation', 'participant_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.UserProfile']))


    def backwards(self, orm):
        
        # Adding model 'Rider'
        db.create_table('stables_rider', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userrider', to=orm['stables.UserProfile'])),
        ))
        db.send_create_signal('stables', ['Rider'])

        # Adding model 'Owner'
        db.create_table('stables_owner', (
            ('userprofile_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.UserProfile'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('stables', ['Owner'])

        # Adding model 'Customer'
        db.create_table('stables_customer', (
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='usercustomer', to=orm['stables.UserProfile'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('stables', ['Customer'])

        # Deleting model 'CustomerInfo'
        db.delete_table('stables_customerinfo')

        # Deleting model 'RiderInfo'
        db.delete_table('stables_riderinfo')

        # Changing field 'Enroll.rider'
        db.alter_column('stables_enroll', 'rider_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Rider']))

        # Adding field 'Horse.owner'
        db.add_column('stables_horse', 'owner', self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['stables.Owner']), keep_default=False)

        # Changing field 'UserProfile.customer'
        db.alter_column('stables_userprofile', 'customer_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.Customer'], unique=True, null=True))

        # Changing field 'UserProfile.rider'
        db.alter_column('stables_userprofile', 'rider_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.Rider'], unique=True, null=True))

        # Changing field 'Course.creator'
        db.alter_column('stables_course', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True))

        # Changing field 'Participation.participant'
        db.alter_column('stables_participation', 'participant_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Rider']))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'schedule.calendar': {
            'Meta': {'object_name': 'Calendar'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200', 'db_index': 'True'})
        },
        'schedule.event': {
            'Meta': {'object_name': 'Event'},
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Calendar']", 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'end_recurring_period': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rule': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Rule']", 'null': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'schedule.rule': {
            'Meta': {'object_name': 'Rule'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'params': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'stables.course': {
            'Meta': {'object_name': 'Course'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.UserProfile']", 'null': 'True'}),
            'default_participation_fee': ('stables.models.CurrencyField', [], {'default': '0.0', 'max_digits': '10', 'decimal_places': '2'}),
            'end': ('django.db.models.fields.DateField', [], {}),
            'events': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['schedule.Event']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'stables.customerinfo': {
            'Meta': {'object_name': 'CustomerInfo'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'stables.enroll': {
            'Meta': {'object_name': 'Enroll'},
            'attended_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 11, 20, 14, 44, 27, 263008)'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Course']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.UserProfile']"}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stables.horse': {
            'Meta': {'object_name': 'Horse'},
            'birthday': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'stables.participation': {
            'Meta': {'object_name': 'Participation'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.UserProfile']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stables.riderinfo': {
            'Meta': {'object_name': 'RiderInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stables.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'stables.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'customer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stables.CustomerInfo']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rider': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stables.RiderInfo']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['stables']
