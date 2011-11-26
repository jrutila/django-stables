# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'UserProfile'
        db.create_table('stables_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('rider', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.Rider'], unique=True, null=True, blank=True)),
            ('customer', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.Customer'], unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('stables', ['UserProfile'])

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
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='usercustomer', to=orm['stables.UserProfile'])),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('stables', ['Customer'])

        # Adding model 'Horse'
        db.create_table('stables_horse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('birthday', self.gf('django.db.models.fields.DateField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Owner'])),
        ))
        db.send_create_signal('stables', ['Horse'])

        # Adding model 'Course'
        db.create_table('stables_course', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')()),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('default_participation_fee', self.gf('stables.models.CurrencyField')(default=0.0, max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('stables', ['Course'])

        # Adding M2M table for field events on 'Course'
        db.create_table('stables_course_events', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('course', models.ForeignKey(orm['stables.course'], null=False)),
            ('event', models.ForeignKey(orm['schedule.event'], null=False))
        ))
        db.create_unique('stables_course_events', ['course_id', 'event_id'])

        # Adding model 'Transaction'
        db.create_table('stables_transaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('stables', ['Transaction'])

        # Adding model 'Participation'
        db.create_table('stables_participation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Rider'])),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schedule.Event'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('stables', ['Participation'])

        # Adding model 'Enroll'
        db.create_table('stables_enroll', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Course'])),
            ('rider', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Rider'])),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('attended_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 11, 20, 14, 7, 43, 105714))),
        ))
        db.send_create_signal('stables', ['Enroll'])


    def backwards(self, orm):
        
        # Deleting model 'UserProfile'
        db.delete_table('stables_userprofile')

        # Deleting model 'Rider'
        db.delete_table('stables_rider')

        # Deleting model 'Owner'
        db.delete_table('stables_owner')

        # Deleting model 'Customer'
        db.delete_table('stables_customer')

        # Deleting model 'Horse'
        db.delete_table('stables_horse')

        # Deleting model 'Course'
        db.delete_table('stables_course')

        # Removing M2M table for field events on 'Course'
        db.delete_table('stables_course_events')

        # Deleting model 'Transaction'
        db.delete_table('stables_transaction')

        # Deleting model 'Participation'
        db.delete_table('stables_participation')

        # Deleting model 'Enroll'
        db.delete_table('stables_enroll')


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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'default_participation_fee': ('stables.models.CurrencyField', [], {'default': '0.0', 'max_digits': '10', 'decimal_places': '2'}),
            'end': ('django.db.models.fields.DateField', [], {}),
            'events': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['schedule.Event']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'stables.customer': {
            'Meta': {'object_name': 'Customer'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'usercustomer'", 'to': "orm['stables.UserProfile']"})
        },
        'stables.enroll': {
            'Meta': {'object_name': 'Enroll'},
            'attended_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 11, 20, 14, 7, 43, 105714)'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Course']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Rider']"}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stables.horse': {
            'Meta': {'object_name': 'Horse'},
            'birthday': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Owner']"})
        },
        'stables.owner': {
            'Meta': {'object_name': 'Owner', '_ormbases': ['stables.UserProfile']},
            'userprofile_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stables.UserProfile']", 'unique': 'True', 'primary_key': 'True'})
        },
        'stables.participation': {
            'Meta': {'object_name': 'Participation'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schedule.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'participant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.Rider']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'stables.rider': {
            'Meta': {'object_name': 'Rider'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userrider'", 'to': "orm['stables.UserProfile']"})
        },
        'stables.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'stables.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'customer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stables.Customer']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rider': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stables.Rider']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['stables']
