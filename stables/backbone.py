from tastypie.resources import ModelResource
from tastypie.resources import Resource
from stables.models import UserProfile
from stables.models import Participation
from stables.models import InstructorParticipation
from stables.models import InstructorInfo
from stables.models import Horse
from stables.models import Transaction
from stables.models import ATTENDING
from schedule.models import Event
from schedule.models import Occurrence
from stables.models import EventMetaData
from stables.models import Accident
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.cache import SimpleCache
from tastypie.authorization import Authorization
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField

from django.db.models.signals import post_save
from django.conf.urls.defaults import url

from django.contrib.comments import Comment
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

import datetime
from django.utils.translation import ugettext as _
from django.db.models import Q
import operator
import json

class UserResource(ModelResource):
    class Meta:
        queryset  = UserProfile.objects.all().prefetch_related('user')
        cache = SimpleCache(timeout=30*60)
    name = fields.CharField()

    def dehydrate_name(self, bundle):
        return bundle.obj.user.first_name + " " + bundle.obj.user.last_name

class EventMetaDataResource(ModelResource):
    class Meta:
        queryset  = EventMetaData.objects.all()
        object_class = EventMetaData
        authorization= Authorization()
        always_return_data = True
    event = fields.ForeignKey("stables.backbone.EventResource", attribute='event')

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj
        return { 'pk': bundle_or_obj.id }

class CommentResource(ModelResource):
    content_object = GenericForeignKeyField({
            EventMetaData: EventMetaDataResource,
        }, 'content_object')

    class Meta:
        queryset = Comment.objects.all()
        model = Comment
        authorization = Authorization()
        filtering = {
            'content_object': [ 'exact', ]
        }
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj
        return { 'pk': bundle_or_obj.id }

    def obj_create(self, bundle, **kwargs):
        kwargs['site'] = Site.objects.get_current()
        return super(CommentResource, self).obj_create(bundle, **kwargs)

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
            self.rider_url = part.participant.get_absolute_url()
            self.rider_id = part.participant.id
            self.state = part.state
            self.event_id = part.event.id
            self.start = part.start
            self.end = part.end
            self.note = part.note

            if part.horse:
                self.horse_id = part.horse.id
            self.finance = "ok"
            self.finance_hint = unicode(saldo[1])
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
            if hasattr(part, 'accident'):
                self.accident_url = part.accident.get_absolute_url

class ApiList(list):
    def all(self):
        return self

class ViewEvent:
    def __init__(self, occ=None, course=None, parts=None, saldos=None, instr=None, metadata=None, last_comment=None, accidents=None):
        self.participations = []
        if occ:
            self.pk = occ.start
            self.start = occ.start
            self.end = occ.end
            self.title = occ.event.title
            self.event_id = occ.event.id
        if instr:
            self.instructor_id = instr.instructor_id
        if parts:
            self.participations = ApiList()
            for p in parts:
                p.saldo = saldos[p.id]
                if p.participant.rider.pk in accidents:
                    setattr(p, 'accident', accidents[p.participant.rider.pk])
                self.participations.append(ViewParticipation(p))
        if metadata:
            self.metadata = metadata
        if last_comment:
            self.last_comment = last_comment.comment
            self.last_comment_date = last_comment.submit_date
            self.last_comment_user = last_comment.user_name


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
    accident_url = fields.CharField(attribute='accident_url', null=True)

    class Meta:
        resource_name = 'participations'
        object_class = ViewParticipation
        always_return_data = True

    def obj_get(self, bundle, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        accidents = Accident.objects.filter(at__lte=part.end, at__gte=part.start, rider=part.participant.rider)
        if accidents:
            setattr(part, 'accident', accidents[0])
        setattr(part, 'saldo', part.get_saldo())
        return ViewParticipation(part)

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
        bundle.obj = ViewParticipation(part)
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
        part.note = bundle.data['note'] if bundle.data['note'] else ""
        part.event = Event.objects.get(pk=bundle.data['event_id'])
        part.start = datetime.datetime.strptime(bundle.data['start'], '%Y-%m-%dT%H:%M:%S')
        part.end = datetime.datetime.strptime(bundle.data['end'], '%Y-%m-%dT%H:%M:%S')
        part.save()
        part = Participation.objects.get(pk=part.id)
        bundle.obj = ViewParticipation(part)
        return bundle

class ShortClientCache(SimpleCache):
    def cache_control(self):
        control = super(ShortClientCache, self).cache_control()
        control['max-age'] = 10
        control['s-maxage'] = 10
        return control

class EventResource(Resource):
    class Meta:
        resource_name = 'events'
        object_class = ViewEvent
        cache = ShortClientCache(timeout=30*60, private=True)
        list_allowed_methods = ['get', 'post']

    start = fields.DateField(attribute='start')
    end = fields.DateField(attribute='end')
    title = fields.CharField(attribute='title')
    event_id = fields.IntegerField(attribute='event_id')
    instructor_id = fields.IntegerField(attribute='instructor_id', null=True)
    participations = fields.ToManyField(ParticipationResource, 'participations', full=True, null=True)
    metadata = fields.ForeignKey(EventMetaDataResource, attribute='metadata', null=True)
    last_comment_user = fields.CharField(attribute='last_comment_user', null=True)
    last_comment_date = fields.DateField(attribute='last_comment_date', null=True)
    last_comment = fields.CharField(attribute='last_comment', null=True)

    def generate_cache_key(self, *args, **kwargs):
        if 'at' in kwargs:
            return "%s:%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, 'at', kwargs['at'])
        return "%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, kwargs['pk'])

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj
        if isinstance(bundle_or_obj, ViewEvent):
            return { 'pk': bundle_or_obj.event_id }
        return { 'pk': bundle_or_obj.id }

    def get_list(self, request, **kwargs):
        """
        Copied from resources.py around line 1265
        """
        base_bundle = self.build_bundle(request=request)
        objects = self.cached_obj_get_list(bundle=base_bundle, at=request.GET.get('at'), **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_uri(), limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()

        # Dehydrate the bundles in preparation for serialization.
        bundles = []

        for obj in to_be_serialized[self._meta.collection_name]:
            bundle = self.build_bundle(obj=obj, request=request)
            bundles.append(self.full_dehydrate(bundle, for_list=True))

        to_be_serialized[self._meta.collection_name] = bundles
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        return self.create_response(request, to_be_serialized)

    def override_urls(self):
        return [
                url(r"^(?P<resource_name>%s)/set/$" %
                    (self._meta.resource_name, ),
                    self.wrap_view('setevent'), name='set_event'),
                ]

    def setevent(self, request, **kwargs):
        obj = json.loads(request.body)
        event_id = obj['event_id']
        start = datetime.datetime.strptime(obj['start'], '%Y-%m-%dT%H:%M:%S')
        end = datetime.datetime.strptime(obj['end'], '%Y-%m-%dT%H:%M:%S')
        part = InstructorParticipation.objects.filter(event_id=event_id, start=start, end=end)
        if obj['instructor_id'] == 0 or obj['instructor_id'] == None:
            if part:
                part.delete()
        else:
            if not part:
                part = InstructorParticipation()
                part.start = start
                part.end = end
                part.event_id = event_id
            else:
                part = part[0]
            part.instructor = InstructorInfo.objects.get(user__id=obj['instructor_id']).user
            part.save()
        return self.create_response(request, {})

    def obj_get_list(self, request=None, **kwargs):
        bundle = kwargs['bundle']
        request = bundle.request
        at = request.GET.get('at')
        occs = []
        if at:
            at = datetime.datetime.strptime(at, '%Y-%m-%d').date()
            start = datetime.datetime.combine(at, datetime.time.min)
            end = datetime.datetime.combine(at, datetime.time.max)
            partids, parts = Participation.objects.generate_participations(start, end)
            instr = list(InstructorParticipation.objects.filter(start__gte=start, end__lte=end))
            instr = dict((i.event.pk, i) for i in instr)
            saldos = dict(Transaction.objects.get_saldos(partids))
            metadatas = dict((e.event.pk, e) for e in EventMetaData.objects.filter(start__gte=start, end__lte=end))
            accidents = dict([ (a.rider.pk, a) for a in Accident.objects.filter(at__gte=start, at__lte=end)])
            comments = {}
            for c in Comment.objects.filter(object_pk__in=[m.pk for m in metadatas.values()], content_type=ContentType.objects.get_for_model(EventMetaData)):
                comments[int(c.object_pk)] = c

            for (o, (c, p)) in parts.items():
                metadata = metadatas.get(o.event.pk, None)
                occs.append(ViewEvent(o, c, p, saldos,
                    instr.get(o.event.pk, None),
                    metadata,
                    comments.get(metadata.pk if metadata else None, None),
                    accidents
                ))
        return occs

    def obj_get(self, bundle, **kwargs):
        ev = Event.objects.get(pk=kwargs['pk'])
        ev.event_id = ev.id
        return ev

def update_event_resource(sender, **kwargs):
    inst = kwargs['instance']
    if hasattr(kwargs['instance'], 'source'):
        inst = kwargs['instance'].source
    time_attrs = ['original_start', 'start', 'at']
    dates = set()
    for ta in time_attrs:
        d = getattr(inst, ta, None)
        if d:
            dates.add(d.strftime('%Y-%m-%d'))
    er = EventResource()
    for d in dates:
        key = er.generate_cache_key(at=d)
        er._meta.cache.set(key, None)

post_save.connect(update_event_resource, sender=Participation)
post_save.connect(update_event_resource, sender=Occurrence)
post_save.connect(update_event_resource, sender=InstructorParticipation)
post_save.connect(update_event_resource, sender=Transaction)
post_save.connect(update_event_resource, sender=Comment)
post_save.connect(update_event_resource, sender=Accident)
