import logging
import datetime
from django.conf.urls import url
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.utils import timezone
from schedule.models import Event, Calendar, Occurrence
from stables.models.accident import Accident
from stables.models.common import Transaction, _count_saldo
from stables.models.event_metadata import EventMetaData
from stables.models.financial import Ticket
from stables.models.participations import InstructorParticipation
from stables.models.participations import Participation
from stables.models.course import Enroll, Course
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource
from tastypie.utils import is_valid_jsonp_callback_value, dict_strip_unicode_keys, trailing_slash
from tastypie import http
from stables.backbone import ApiList, ShortClientCache, ParticipationPermissionAuthentication
from stables.backbone.occurrence import EventMetaDataResource
from stables.backbone.participation import ViewParticipation, ParticipationResource
from django.utils.translation import ugettext as _
from dateutil import parser
from stables.models.user import InstructorInfo

__author__ = 'jorutila'

logger = logging.getLogger(__name__)

class ViewEvent:
    def __init__(self, occ=None, course=None, parts=None, saldos=None, instr=None, metadata=None, last_comment=None, accidents=None, ticketcounts=None, warnings=None, enrolls=[]):
        self.participations = []
        if occ:
            self.pk = occ.start
            logger.debug("Current timezone: %s" % timezone.get_current_timezone())
            logger.debug("occ: %s" % occ.start.tzinfo)
            self.start = timezone.get_current_timezone().normalize(occ.start)
            self.end = timezone.get_current_timezone().normalize(occ.end)
            self.title = occ.event.title
            self.event_id = occ.event.id
            self.cancelled = occ.cancelled
            self.id = str(occ.event.id) + "-" + timezone.utc.normalize(occ.start.astimezone(timezone.utc)).isoformat()
        if instr:
            self.instructor_id = instr.id
        if parts and not self.cancelled:
            self.participations = ApiList()
            for p in parts:
                p.saldo = saldos[p.id]
                if p.participant.rider and p.participant.rider.pk in accidents:
                    setattr(p, 'accident', accidents[p.participant.rider.pk])
                if ticketcounts and p.pk in ticketcounts and ticketcounts[p.pk] <= 1:
                    warnings[p.pk] = _('%d tickets remaining') % ticketcounts[p.pk]
                if warnings and p.pk in warnings:
                    setattr(p, 'warning', warnings[p.pk])
                if enrolls:
                    enroll = [ e for e in enrolls if e.participant == p.participant ]
                    if len(enroll) > 0:
                        setattr(p, "enroll", enroll[0])
                self.participations.append(ViewParticipation(p))
        if course:
            self.course_id = course.id
        elif occ and occ.event.course_set.count() > 0:
            self.course_id = occ.event.course_set.all()[0].id
        else:
            self.course_id = 0
        if metadata:
            self.metadata = metadata
        if last_comment:
            self.last_comment = last_comment.comment
            self.last_comment_date = last_comment.submit_date
            self.last_comment_user = last_comment.user_name

def _get_transactions(participations):
    return Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id__in=participations).order_by('object_id', 'created_on').select_related().prefetch_related('ticket_set__type', 'ticket_set__owner')

def _get_saldos(participations):
    ret = {}
    trans = list(_get_transactions(participations))
    ids = participations
    for (pid, tt) in [(x, [y for y in trans if y.object_id==x]) for x in ids]:
        ret[pid] = _count_saldo(tt)
    return ret

class EventResource(Resource):
    class Meta:
        resource_name = 'events'
        object_class = ViewEvent
        cache = ShortClientCache(timeout=30*60, private=True)
        list_allowed_methods = ['get', 'post', 'put']
        allowed_methods = ['get', 'post']
        move_allowed_methods = ['post']
        options_allowed_methods = ['put']
        authentication = ParticipationPermissionAuthentication()
        always_return_data = True

    id = fields.CharField(attribute='id')
    start = fields.DateField(attribute='start')
    end = fields.DateField(attribute='end')
    cancelled = fields.BooleanField(attribute='cancelled', null=True)
    title = fields.CharField(attribute='title')
    event_id = fields.IntegerField(attribute='event_id')
    course_id = fields.IntegerField(attribute='course_id')
    instructor_id = fields.IntegerField(attribute='instructor_id', null=True)
    participations = fields.ToManyField(ParticipationResource, 'participations', full=True, null=True)
    metadata = fields.ForeignKey(EventMetaDataResource, attribute='metadata', null=True)
    last_comment_user = fields.CharField(attribute='last_comment_user', null=True)
    last_comment_date = fields.DateField(attribute='last_comment_date', null=True)
    last_comment = fields.CharField(attribute='last_comment', null=True)
    #course_url = fields.CharField(attribute='course', null=True)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<%s>\d*-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}.*)/move%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_move'), name="api_move_event"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\d*-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}.*)/options%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_options'), name="api_options"),
            url(r"^(?P<resource_name>%s)/(?P<%s>\d*-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}.*)%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            ]

    def generate_cache_key(self, *args, **kwargs):
        if 'at' in kwargs:
            return "%s:%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, 'at', kwargs['at'])
        return "%s:%s:%s" % (self._meta.api_name, self._meta.resource_name, kwargs['pk'])

    def _get_id_data(self, pk):
        import re
        m = re.search("(\d*)-(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}.*)", pk)
        eid = int(m.group(1))
        date = timezone.localtime(parser.parse(m.group(2)))
        return { 'id': eid, 'start': date }

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj
        return {'pk': bundle_or_obj.id}

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

    def obj_get_list(self, request=None, **kwargs):
        bundle = kwargs['bundle']
        request = bundle.request
        at = request.GET.get('at')
        occs = []
        if at:
            at = datetime.datetime.strptime(at, '%Y-%m-%d').date()
            start = timezone.get_current_timezone().localize(
                datetime.datetime.combine(at, datetime.time.min))
            end = timezone.get_current_timezone().localize(
                datetime.datetime.combine(at, datetime.time.max))
            logger.debug("Generating participations on %s to %s" % (start, end))
            partids, parts = Participation.objects.generate_participations(
                start, end)
            instr = list(InstructorParticipation.objects.filter(start__gte=start, end__lte=end))
            instr = dict((i.event.pk, i) for i in instr)
            saldos = dict(_get_saldos(partids))
            ticketcounts = Ticket.objects.get_ticketcounts(partids)
            metadatas = dict((e.event.pk, e) for e in EventMetaData.objects.filter(start__gte=start, end__lte=end))
            accidents = dict([ (a.rider.pk, a) for a in Accident.objects.filter(at__gte=start, at__lte=end)])
            warnings = Participation.objects.generate_warnings(start, end)
            comments = {}
            courses = (c for (o, c, p) in parts)
            enrolls = list(Enroll.objects.filter(course__in=courses))

            for (o, c, p) in parts:
                logger.debug("Found occ: %s %s" % (o, o.event.title))
                metadata = metadatas.get(o.event.pk, None)
                ins = instr.get(o.event.pk, None)
                occs.append(ViewEvent(o, c, p, saldos,
                                      ins.instructor if ins else None,
                                      metadata,
                                      comments.get(metadata.pk if metadata else None, None),
                                      accidents,
                                      ticketcounts,
                                      warnings,
                                      enrolls
                ))
        return occs

    def _occ_stuff_(self, occ):
        parts = Participation.objects.get_participations(occ)
        saldos = dict(_get_saldos([p.id for p in parts ]))
        accidents = dict([ (a.rider.pk, a) for a in Accident.objects.filter(at__gte=occ.start, at__lte=occ.end)])
        instr = list(InstructorParticipation.objects.filter(start__gte=occ.start, end__lte=occ.end))
        instr = dict((i.event.pk, i) for i in instr)
        return { "parts": parts, "saldos": saldos, "accidents": accidents, "instr": instr }

    def obj_get(self, bundle, **kwargs):
        id_data = self._get_id_data(kwargs['pk'])
        ev = Event.objects.get(id=id_data['id'])
        occ = ev.get_occurrence(id_data['start'])
        stuff = self._occ_stuff_(occ)
        return ViewEvent(occ=occ, **stuff)

    def obj_create(self, bundle, **kwargs):
        data = bundle.data
        data['calendar'] = Calendar.objects.get(slug='main')
        import pytz
        data['start'] = parser.parse(data['start'], tzinfos={'UTC': pytz.UTC})
        data['end'] = parser.parse(data['end'], tzinfos={'UTC': pytz.UTC})
        course = None
        if 'course' in data and data['course']:
            course = Course.objects.get(pk=data['course'])
            data['title'] = course.name
            del data['course']
        event = Event.objects.create(**data)
        if course:
            course.events.add(event)
        bundle.obj=ViewEvent(occ=event.get_occurrence(event.start))
        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        data = bundle.data
        id_data = self._get_id_data(kwargs['pk'])
        ev = Event.objects.get(id=id_data['id'])
        occ = ev.get_occurrence(id_data['start'])
        bundle.obj = ViewEvent(occ=occ)
        return bundle

    def dispatch_move(self, request, **kwargs):
        return self.dispatch("move", request, **kwargs)

    def post_move(self, request, **kwargs):
        deserialized = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized), request=request)

        data = bundle.data
        id_data = self._get_id_data(kwargs['pk'])
        ev = Event.objects.get(id=id_data['id'])
        occ = ev.get_occurrence(id_data['start'])
        if not occ:
            gen = ev.occurrences_after(id_data['start'])
            occ = next(gen)

        stuff = {}
        if not occ.cancelled and 'cancelled' in data and data['cancelled']:
            occ.cancel()
        elif occ.cancelled and 'cancelled' in data and not data['cancelled']:
            occ.uncancel()
            stuff = self._occ_stuff_(occ)
        elif not occ.cancelled and 'start' in data and 'end' in data:
            tz = timezone.get_current_timezone()
            new_start = timezone.make_aware(datetime.datetime.strptime(data['start'], '%Y-%m-%dT%H:%M'), tz)
            new_end = timezone.make_aware(datetime.datetime.strptime(data['end'], '%Y-%m-%dT%H:%M'), tz)
            occ.move(new_start, new_end)

        obj = ViewEvent(occ=occ, **stuff)
        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)

        return self.create_response(request, bundle)

    def dispatch_options(self, request, **kwargs):
        return self.dispatch("options", request, **kwargs)

    def put_options(self, request, **kwargs):
        deserialized = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized), request=request)

        data = bundle.data
        id_data = self._get_id_data(kwargs['pk'])
        ev = Event.objects.get(id=id_data['id'])
        occ = ev.get_occurrence(id_data['start'])

        part = InstructorParticipation.objects.filter(event=ev, start=occ.start, end=occ.end)
        if data['instructor'] == 0 or data['instructor'] == None:
            if part:
                part.delete()
        else:
            if not part:
                part = InstructorParticipation()
                part.start = occ.start
                part.end = occ.end
                part.event = ev
            else:
                part = part[0]
            part.instructor = InstructorInfo.objects.get(user__id=data['instructor']).user
            part.save()

        obj = ViewEvent(occ=occ, instr=part.instructor)
        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        return self.create_response(request, bundle)

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

def enroll_update_cache_clear(sender, **kwargs):
    er = EventResource()

post_save.connect(update_event_resource, sender=Participation)
post_save.connect(update_event_resource, sender=Occurrence)
post_save.connect(update_event_resource, sender=InstructorParticipation)
post_save.connect(update_event_resource, sender=Transaction)
post_save.connect(update_event_resource, sender=Accident)
post_save.connect(update_event_resource, sender=Event)
