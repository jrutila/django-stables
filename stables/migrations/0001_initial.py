# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'RiderLevel'
        db.create_table(u'stables_riderlevel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('stables', ['RiderLevel'])

        # Adding M2M table for field includes on 'RiderLevel'
        m2m_table_name = db.shorten_name(u'stables_riderlevel_includes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_riderlevel', models.ForeignKey(orm['stables.riderlevel'], null=False)),
            ('to_riderlevel', models.ForeignKey(orm['stables.riderlevel'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_riderlevel_id', 'to_riderlevel_id'])

        # Adding model 'UserProfile'
        db.create_table(u'stables_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('rider', self.gf('django.db.models.fields.related.OneToOneField')(related_name='user', null=True, on_delete=models.SET_NULL, to=orm['stables.RiderInfo'], blank=True, unique=True)),
            ('customer', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['stables.CustomerInfo'], unique=True, null=True, on_delete=models.SET_NULL, blank=True)),
            ('instructor', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='user', unique=True, null=True, to=orm['stables.InstructorInfo'])),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
        ))
        db.send_create_signal('stables', ['UserProfile'])

        # Adding model 'CustomerInfo'
        db.create_table(u'stables_customerinfo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('stables', ['CustomerInfo'])

        # Adding model 'RiderInfo'
        db.create_table(u'stables_riderinfo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('customer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.CustomerInfo'])),
        ))
        db.send_create_signal('stables', ['RiderInfo'])

        # Adding M2M table for field levels on 'RiderInfo'
        m2m_table_name = db.shorten_name(u'stables_riderinfo_levels')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('riderinfo', models.ForeignKey(orm['stables.riderinfo'], null=False)),
            ('riderlevel', models.ForeignKey(orm['stables.riderlevel'], null=False))
        ))
        db.create_unique(m2m_table_name, ['riderinfo_id', 'riderlevel_id'])

        # Adding model 'InstructorInfo'
        db.create_table(u'stables_instructorinfo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('stables', ['InstructorInfo'])

        # Adding model 'TicketType'
        db.create_table(u'stables_tickettype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('stables', ['TicketType'])

        # Adding model 'Ticket'
        db.create_table(u'stables_ticket', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.TicketType'])),
            ('owner_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('owner_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('transaction', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ticket_set', null=True, to=orm['stables.Transaction'])),
            ('expires', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 20, 0, 0), null=True, blank=True)),
        ))
        db.send_create_signal('stables', ['Ticket'])

        # Adding model 'Horse'
        db.create_table(u'stables_horse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('last_usage_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('stables', ['Horse'])

        # Adding model 'Course'
        db.create_table(u'stables_course', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('max_participants', self.gf('django.db.models.fields.IntegerField')(default=7)),
            ('default_participation_fee', self.gf('stables.models.financial.CurrencyField')(default=0, max_digits=10, decimal_places=2)),
            ('course_fee', self.gf('stables.models.financial.CurrencyField')(default=0, max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('stables', ['Course'])

        # Adding M2M table for field events on 'Course'
        m2m_table_name = db.shorten_name(u'stables_course_events')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('course', models.ForeignKey(orm['stables.course'], null=False)),
            ('event', models.ForeignKey(orm['schedule.event'], null=False))
        ))
        db.create_unique(m2m_table_name, ['course_id', 'event_id'])

        # Adding M2M table for field ticket_type on 'Course'
        m2m_table_name = db.shorten_name(u'stables_course_ticket_type')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('course', models.ForeignKey(orm['stables.course'], null=False)),
            ('tickettype', models.ForeignKey(orm['stables.tickettype'], null=False))
        ))
        db.create_unique(m2m_table_name, ['course_id', 'tickettype_id'])

        # Adding M2M table for field allowed_levels on 'Course'
        m2m_table_name = db.shorten_name(u'stables_course_allowed_levels')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('course', models.ForeignKey(orm['stables.course'], null=False)),
            ('riderlevel', models.ForeignKey(orm['stables.riderlevel'], null=False))
        ))
        db.create_unique(m2m_table_name, ['course_id', 'riderlevel_id'])

        # Adding model 'Enroll'
        db.create_table(u'stables_enroll', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Course'])),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.UserProfile'])),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=6)),
            ('last_state_change_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 20, 0, 0))),
        ))
        db.send_create_signal('stables', ['Enroll'])

        # Adding model 'CourseParticipationActivator'
        db.create_table(u'stables_courseparticipationactivator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('enroll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Enroll'])),
            ('activate_before_hours', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('stables', ['CourseParticipationActivator'])

        # Adding model 'Participation'
        db.create_table(u'stables_participation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('participant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.UserProfile'])),
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schedule.Event'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
            ('last_state_change_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('horse', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Horse'], null=True, blank=True)),
        ))
        db.send_create_signal('stables', ['Participation'])

        # Adding unique constraint on 'Participation', fields ['participant', 'event', 'start', 'end']
        db.create_unique(u'stables_participation', ['participant_id', 'event_id', 'start', 'end'])

        # Adding model 'InstructorParticipation'
        db.create_table(u'stables_instructorparticipation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instructor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.UserProfile'])),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schedule.Event'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('stables', ['InstructorParticipation'])

        # Adding model 'EventMetaData'
        db.create_table(u'stables_eventmetadata', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schedule.Event'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
            ('notes', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('stables', ['EventMetaData'])

        # Adding model 'ParticipationTransactionActivator'
        db.create_table(u'stables_participationtransactionactivator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('participation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Participation'])),
            ('activate_before_hours', self.gf('django.db.models.fields.IntegerField')()),
            ('fee', self.gf('stables.models.financial.CurrencyField')(max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('stables', ['ParticipationTransactionActivator'])

        # Adding M2M table for field ticket_type on 'ParticipationTransactionActivator'
        m2m_table_name = db.shorten_name(u'stables_participationtransactionactivator_ticket_type')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('participationtransactionactivator', models.ForeignKey(orm['stables.participationtransactionactivator'], null=False)),
            ('tickettype', models.ForeignKey(orm['stables.tickettype'], null=False))
        ))
        db.create_unique(m2m_table_name, ['participationtransactionactivator_id', 'tickettype_id'])

        # Adding model 'CourseTransactionActivator'
        db.create_table(u'stables_coursetransactionactivator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('enroll', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Enroll'])),
            ('fee', self.gf('stables.models.financial.CurrencyField')(max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('stables', ['CourseTransactionActivator'])

        # Adding model 'Transaction'
        db.create_table(u'stables_transaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('customer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.CustomerInfo'])),
            ('amount', self.gf('stables.models.financial.CurrencyField')(max_digits=10, decimal_places=2)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('stables', ['Transaction'])

        # Adding model 'AccidentType'
        db.create_table(u'stables_accidenttype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('stables.models.accident.I18NCharField')(max_length=1000)),
        ))
        db.send_create_signal('stables', ['AccidentType'])

        # Adding model 'Accident'
        db.create_table(u'stables_accident', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.AccidentType'])),
            ('at', self.gf('django.db.models.fields.DateTimeField')()),
            ('rider', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.RiderInfo'])),
            ('horse', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.Horse'])),
            ('instructor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stables.InstructorInfo'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('stables', ['Accident'])


    def backwards(self, orm):
        # Removing unique constraint on 'Participation', fields ['participant', 'event', 'start', 'end']
        db.delete_unique(u'stables_participation', ['participant_id', 'event_id', 'start', 'end'])

        # Deleting model 'RiderLevel'
        db.delete_table(u'stables_riderlevel')

        # Removing M2M table for field includes on 'RiderLevel'
        db.delete_table(db.shorten_name(u'stables_riderlevel_includes'))

        # Deleting model 'UserProfile'
        db.delete_table(u'stables_userprofile')

        # Deleting model 'CustomerInfo'
        db.delete_table(u'stables_customerinfo')

        # Deleting model 'RiderInfo'
        db.delete_table(u'stables_riderinfo')

        # Removing M2M table for field levels on 'RiderInfo'
        db.delete_table(db.shorten_name(u'stables_riderinfo_levels'))

        # Deleting model 'InstructorInfo'
        db.delete_table(u'stables_instructorinfo')

        # Deleting model 'TicketType'
        db.delete_table(u'stables_tickettype')

        # Deleting model 'Ticket'
        db.delete_table(u'stables_ticket')

        # Deleting model 'Horse'
        db.delete_table(u'stables_horse')

        # Deleting model 'Course'
        db.delete_table(u'stables_course')

        # Removing M2M table for field events on 'Course'
        db.delete_table(db.shorten_name(u'stables_course_events'))

        # Removing M2M table for field ticket_type on 'Course'
        db.delete_table(db.shorten_name(u'stables_course_ticket_type'))

        # Removing M2M table for field allowed_levels on 'Course'
        db.delete_table(db.shorten_name(u'stables_course_allowed_levels'))

        # Deleting model 'Enroll'
        db.delete_table(u'stables_enroll')

        # Deleting model 'CourseParticipationActivator'
        db.delete_table(u'stables_courseparticipationactivator')

        # Deleting model 'Participation'
        db.delete_table(u'stables_participation')

        # Deleting model 'InstructorParticipation'
        db.delete_table(u'stables_instructorparticipation')

        # Deleting model 'EventMetaData'
        db.delete_table(u'stables_eventmetadata')

        # Deleting model 'ParticipationTransactionActivator'
        db.delete_table(u'stables_participationtransactionactivator')

        # Removing M2M table for field ticket_type on 'ParticipationTransactionActivator'
        db.delete_table(db.shorten_name(u'stables_participationtransactionactivator_ticket_type'))

        # Deleting model 'CourseTransactionActivator'
        db.delete_table(u'stables_coursetransactionactivator')

        # Deleting model 'Transaction'
        db.delete_table(u'stables_transaction')

        # Deleting model 'AccidentType'
        db.delete_table(u'stables_accidenttype')

        # Deleting model 'Accident'
        db.delete_table(u'stables_accident')


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
            'last_state_change_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 20, 0, 0)'}),
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
            'expires': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 20, 0, 0)', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'owner_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'transaction': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ticket_set'", 'null': 'True', 'to': "orm['stables.Transaction']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stables.TicketType']"})
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
            'customer': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['stables.CustomerInfo']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instructor': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'user'", 'unique': 'True', 'null': 'True', 'to': "orm['stables.InstructorInfo']"}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'rider': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'user'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['stables.RiderInfo']", 'blank': 'True', 'unique': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['stables']