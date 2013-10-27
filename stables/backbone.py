from tastypie.resources import ModelResource
from tastypie.resources import Resource
from stables.models import UserProfile
from stables.models import Participation
from stables.models import Horse
from stables.models import Transaction
from stables.models import ATTENDING
from schedule.models import Event
from tastypie import fields
from tastypie.bundle import Bundle
import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
import operator

class UserResource(ModelResource):
    class Meta:
        queryset  = UserProfile.objects.all().prefetch_related('user')
    name = fields.CharField()

    def dehydrate_name(self, bundle):
        return bundle.obj.user.first_name + " " + bundle.obj.user.last_name

class ViewParticipation:
    def __init__(self, part=None, saldo=None):
        self.id = 0
        if part:
            self.id = part.id
            self.rider_name = unicode(part.participant)
            self.rider_url = part.participant.get_absolute_url()
            self.rider_id = part.participant.id
            self.state = part.state
            self.event_id = part.event.id
            self.start = part.start
            self.end = part.end

            if part.horse:
                self.horse_id = part.horse.id
            self.finance = "ok"
            self.finance_hint = saldo[1]
            if (saldo[0] == 0 and saldo[1] == None):
                self.finance_hint = _("Cash")
            saldo = saldo[0]
            if saldo != None and saldo != 0:
                self.finance = saldo
                self.alert_level = 'info'
            if saldo == None and self.state == ATTENDING:
                self.alert_level = 'info'
                self.finance = "--"
            if part.id:
                self.finance_url = part.get_absolute_url()
            self.part = part

class ApiList(list):
    def all(self):
        return self

class ViewEvent:
    def __init__(self, occ=None, course=None, parts=None, saldos=None):
        self.participations = []
        if occ:
            self.pk = occ.start
            self.start = occ.start
            self.end = occ.end
            self.title = occ.event.title
            self.event_id = occ.event.id
        if parts:
            self.participations = ApiList([ ViewParticipation(p, saldos[p.id]) for p in parts])

class ParticipationResource(Resource):
    id = fields.IntegerField(attribute='id', null=True)
    rider_name = fields.CharField(attribute='rider_name')
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

    class Meta:
        resource_name = 'participations'
        object_class = ViewParticipation
        always_return_data = True

    def obj_get(self, bundle, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        return ViewParticipation(part, part.get_saldo())

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
           kwargs['pk'] = bundle_or_obj.obj.id
        else:
           kwargs['pk'] = bundle_or_obj.id

        return kwargs

    def obj_update(self, bundle, request=None, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        part.state = bundle.data['state']
        if bundle.data['horse'] == '0' or bundle.data['horse'] == None:
            part.horse = None
        else:
            part.horse = Horse.objects.get(pk=bundle.data['horse'])
        part.note = bundle.data['note']
        part.save()
        part = Participation.objects.get(pk=kwargs['pk'])
        bundle.obj = ViewParticipation(part, part.get_saldo())
        return bundle

    def obj_create(self, bundle, request=None, **kwargs):
        part = Participation()
        part.state = bundle.data['state']
        if ('rider_id' not in bundle.data and bundle.data['rider_name'] != None):
            f = []
            for v in bundle.data['rider_name'].split(" "):
                f.append((Q(user__first_name__icontains=v) | Q(user__last_name__icontains=v)))
            part.participant = UserProfile.objects.get(reduce(operator.and_, f))
        else:
            part.participant = UserProfile.objects.get(pk=bundle.data['rider_id'])
        if (bundle.data['horse'] and int(bundle.data['horse']) > 0):
            part.horse = Horse.objects.get(pk=bundle.data['horse'])
        part.note = bundle.data['note']
        part.event = Event.objects.get(pk=bundle.data['event_id'])
        part.start = datetime.datetime.strptime(bundle.data['start'], '%Y-%m-%dT%H:%M:%S')
        part.end = datetime.datetime.strptime(bundle.data['end'], '%Y-%m-%dT%H:%M:%S')
        part.save()
        part = Participation.objects.get(pk=part.id)
        bundle.obj = ViewParticipation(part, part.get_saldo())
        return bundle

class EventResource(Resource):
    class Meta:
        resource_name = 'events'
        object_class = ViewEvent

    start = fields.DateField(attribute='start')
    end = fields.DateField(attribute='end')
    title = fields.CharField(attribute='title')
    event_id = fields.IntegerField(attribute='event_id')
    participations = fields.ToManyField(ParticipationResource, 'participations', full=True, null=True)

    def obj_get_list(self, request=None, **kwargs):
        bundle = kwargs['bundle']
        request = bundle.request
        at = request.GET.get('at')
        occs = []
        if at:
            at = datetime.datetime.strptime(at, '%Y-%m-%d').date()
            partids, parts = Participation.objects.generate_participations(
                            datetime.datetime.combine(at, datetime.time.min),
                            datetime.datetime.combine(at, datetime.time.max))
            saldos = dict(Transaction.objects.get_saldos(partids))
            for (o, (c, p)) in parts.items():
                occs.append(ViewEvent(o, c, p, saldos))
        return occs
