from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext as _
from schedule.models.events import Event
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpBadRequest
from stables.models.user import UserProfile
from stables.models.horse import Horse
from tastypie.bundle import Bundle
from stables.models.course import Enroll
from stables.models.financial import Ticket
from stables.models.accident import Accident
from stables.models.participations import Participation
from stables.backbone import ParticipationPermissionAuthentication
from tastypie import fields
from tastypie.resources import Resource
from stables.backbone.enroll import EnrollResource
from stables.models import CANCELED, RESERVED, ATTENDING

__author__ = 'jorutila'

class ViewParticipation:
    def __init__(self, part=None):
        self.id = 0
        if part:
            saldo = None
            if hasattr(part, 'saldo'):
                saldo = part.saldo
            else:
                saldo = part.get_saldo()
            self.id = part.id
            self.rider_name = unicode(part.participant)
            self.rider_phone = part.participant.phone_number
            self.rider_url = part.participant.get_absolute_url()
            self.rider_id = part.participant.id
            self.state = part.state
            self.event_id = part.event.id
            self.start = part.start
            self.end = part.end
            self.note = part.note

            if part.horse:
                self.horse_id = part.horse.id
            if hasattr(part, 'warning'):
                self.alert_level = 'warning'
                self.warning = part.warning

            if (saldo[1]):
                self.finance_hint = unicode(saldo[1])
            elif saldo[2] > Decimal('0.00'):
                try:
                    method = part.get_pay_transaction().method or _('Cash')
                    method = method.title()
                except IndexError:
                    method = _('Cash')
                self.finance_hint = method + ' ' + str(saldo[2])
            elif saldo[2] == Decimal('0.00'):
                self.finance_hint = str(saldo[2])
            else:
                self.finance_hint = '--'

            if (saldo[0] == Decimal('0.00')):
                self.finance = "ok"
            elif (saldo[0] != None and saldo[0] < Decimal('0.00')):
                self.finance = str(saldo[0])
                self.alert_level = 'info'
                self.finance_hint = '--'
            else:
                self.finance = '--'
                self.alert_level = 'info'
            if part.state == CANCELED or part.state == RESERVED:
                self.alert_level = ''

            if part.id:
                self.finance_url = part.get_absolute_url()
            if hasattr(part, 'accident'):
                self.accident_url = part.accident.get_absolute_url
            if hasattr(part, 'enroll') and part.enroll.state == ATTENDING:
                self.enroll = EnrollResource().get_resource_uri(part.enroll)
            else:
                self.enroll = None

class ParticipationResource(Resource):
    id = fields.IntegerField(attribute='id', null=True)
    rider_name = fields.CharField(attribute='rider_name')
    rider_phone = fields.CharField(attribute='rider_phone', null=True)
    rider_id = fields.IntegerField(attribute='rider_id', null=True)
    rider_url = fields.CharField(attribute='rider_url', null=True)
    state = fields.IntegerField(attribute='state')
    horse = fields.IntegerField(attribute='horse_id', null=True)
    finance = fields.CharField(attribute='finance', null=True)
    finance_hint = fields.CharField(attribute='finance_hint', null=True)
    finance_url = fields.CharField(attribute='finance_url', null=True)
    alert_level = fields.CharField(attribute='alert_level', null=True)
    event_id = fields.IntegerField(attribute='event_id')
    start = fields.DateField(attribute='start')
    end = fields.DateField(attribute='end')
    note = fields.CharField(attribute='note', null=True)
    accident_url = fields.CharField(attribute='accident_url', null=True)
    warning = fields.CharField(attribute='warning', null=True)
    enroll = fields.CharField(attribute='enroll', null=True)

    class Meta:
        resource_name = 'participations'
        object_class = ViewParticipation
        always_return_data = True
        authentication = ParticipationPermissionAuthentication()

    def obj_get(self, bundle, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        self._set_extra(part)
        return ViewParticipation(part)

    def _set_extra(self, part):
        accidents = Accident.objects.filter(at__lte=part.end, at__gte=part.start, rider=part.participant.rider)
        ticketcounts = Ticket.objects.get_ticketcounts([part.pk])
        if accidents:
            setattr(part, 'accident', accidents[0])
        # TODO: This logic is now twice
        if ticketcounts and part.pk in ticketcounts and ticketcounts[part.pk] <= 1:
            part.alert_level = 'warning'
            part.warning = _('%d tickets remaining') % ticketcounts[part.pk]
        setattr(part, 'saldo', part.get_saldo())
        course = part.event.course_set.all()
        if course:
            enroll = Enroll.objects.filter(participant=part.participant, course=course[0])
            if enroll:
                setattr(part, 'enroll', enroll[0])

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.id
        else:
            kwargs['pk'] = bundle_or_obj.id

        return kwargs

    def obj_update(self, bundle, request=None, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        part.state = int(bundle.data['state'])
        if bundle.data['horse'] == '0' or bundle.data['horse'] == None:
            part.horse = None
        else:
            part.horse = Horse.objects.get(pk=bundle.data['horse'])
        part.note = bundle.data['note']
        part.save()
        part = Participation.objects.get(pk=kwargs['pk'])
        self._set_extra(part)
        bundle.obj = ViewParticipation(part)
        return bundle

    def obj_create(self, bundle, request=None, **kwargs):
        from dateutil.parser import parse
        event = Event.objects.get(pk=bundle.data['event_id'])
        #start = datetime.datetime.strptime(bundle.data['start'], '%Y-%m-%dT%H:%M:%S')
        start = timezone.make_aware((parse(bundle.data['start'])), timezone.get_current_timezone())
        occ = event.occurrences_after(start).next()
        assert occ.start == start, 'Start time mismatch %s and %s' % (start, occ.start)
        state = int(bundle.data['state'])
        if ('rider_id' not in bundle.data and bundle.data['rider_name'] != None):
            try:
                participant = UserProfile.objects.find(bundle.data['rider_name'])
            except UserProfile.DoesNotExist:
                first_name = bundle.data['rider_name'].split(' ', 1)[0].capitalize()
                last_name = bundle.data['rider_name'].split(' ', 1)[1].capitalize()
                user = User.objects.create(first_name=first_name, last_name=last_name)
                upr,created = UserProfile.objects.get_or_create(user=user)
                if created: upr.save()
                participant = user.get_profile()
                assert participant is not None
            except UserProfile.MultipleObjectsReturned:
                raise ImmediateHttpResponse(HttpBadRequest("Given user is too ambiquous"))
        else:
            participant = UserProfile.objects.get(pk=bundle.data['rider_id'])

        # Create the participation through course
        part = Participation.objects.create_participation(participant, occ, state, True)

        if (bundle.data['horse'] and int(bundle.data['horse']) > 0):
            part.horse = Horse.objects.get(pk=bundle.data['horse'])
        part.note = bundle.data['note'] if bundle.data['note'] else ""
        part.save()
        part = Participation.objects.get(pk=part.id)
        self._set_extra(part)
        bundle.obj = ViewParticipation(part)
        return bundle
