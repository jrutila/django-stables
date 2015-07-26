import logging
import datetime
from django.conf.urls import url
from django.contrib.comments import Comment
from django.db.models.signals import post_save
from django.utils import timezone
from schedule.models import Event, Calendar, Occurrence
from stables.models import EventMetaData, Course
from stables.models.accident import Accident
from stables.models.financial import Transaction, Ticket
from stables.models.participations import InstructorParticipation
from stables.models.participations import Participation
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource
from tastypie.utils import trailing_slash
from stables.backbone import ApiList, ShortClientCache, ParticipationPermissionAuthentication
from stables.backbone.occurrence import EventMetaDataResource
from stables.backbone.participation import ViewParticipation, ParticipationResource
from django.utils.translation import ugettext as _
from dateutil import parser
from stables.models.user import InstructorInfo

__author__ = 'jorutila'

logger = logging.getLogger(__name__)

class ViewEvent:
    def __init__(self, occ=None, course=None, parts=None, saldos=None, instr=None, metadata=None, last_comment=None, accidents=None, ticketcounts=None, warnings=None):
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
            self.instructor_id = instr.instructor_id
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
                self.participations.append(ViewParticipation(p))
        if course:
            pass#self.course = course.get_absolute_url()
        if metadata:
            self.metadata = metadata
        if last_comment:
            self.last_comment = last_comment.comment
            self.last_comment_date = last_comment.submit_date
            self.last_comment_user = last_comment.user_name

class EventResource(Resource):
    class Meta:
        resource_name = 'events'
        object_class = ViewEvent
        cache = ShortClientCache(timeout=30*60, private=True)
        list_allowed_methods = ['get', 'post', 'put']
        allowed_methods = ['get', 'post']
        authentication = ParticipationPermissionAuthentication()
        always_return_data = True

    id = fields.CharField(attribute='id')
    start = fields.DateField(attribute='start')
    end = fields.DateField(attribute='end')
    cancelled = fields.BooleanField(attribute='cancelled', null=True)
    title = fields.CharField(attribute='title')
    event_id = fields.IntegerField(attribute='event_id')
    instructor_id = fields.IntegerField(attribute='instructor_id', null=True)
    participations = fields.ToManyField(ParticipationResource, 'participations', full=True, null=True)
    metadata = fields.ForeignKey(EventMetaDataResource, attribute='metadata', null=True)
    last_comment_user = fields.CharField(attribute='last_comment_user', null=True)
    last_comment_date = fields.DateField(attribute='last_comment_date', null=True)
    last_comment = fields.CharField(attribute='last_comment', null=True)
    course_url = fields.CharField(attribute='course', null=True)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<%s>\d*-\d{4}-\d{2}-\d{2}T\d{2}:\d{2}.*)/move%s$" % (self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()), self.wrap_view('move_event'), name="api_move_event"),
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
            saldos = dict(Transaction.objects.get_saldos(partids))
            ticketcounts = Ticket.objects.get_ticketcounts(partids)
            metadatas = dict((e.event.pk, e) for e in EventMetaData.objects.filter(start__gte=start, end__lte=end))
            accidents = dict([ (a.rider.pk, a) for a in Accident.objects.filter(at__gte=start, at__lte=end)])
            warnings = Participation.objects.generate_warnings(start, end)
            comments = {}
            #for c in Comment.objects.filter(object_pk__in=[m.pk for m in metadatas.values()], content_type=ContentType.objects.get_for_model(EventMetaData)):
            #comments[int(c.object_pk)] = c

            for (o, (c, p)) in parts.items():
                logger.debug("Found occ: %s %s" % (o, o.event.title))
                metadata = metadatas.get(o.event.pk, None)
                occs.append(ViewEvent(o, c, p, saldos,
                                      instr.get(o.event.pk, None),
                                      metadata,
                                      comments.get(metadata.pk if metadata else None, None),
                                      accidents,
                                      ticketcounts,
                                      warnings
                ))
        return occs

    def obj_get(self, bundle, **kwargs):
        id_data = self._get_id_data(kwargs['pk'])
        ev = Event.objects.get(id=id_data['id'])
        occ = ev.get_occurrence(id_data['start'])
        return ViewEvent(occ=occ)

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
        part = InstructorParticipation.objects.filter(event=ev, start=occ.start, end=occ.end)
        if data['instructor_id'] == 0 or data['instructor_id'] == None:
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
            part.instructor = InstructorInfo.objects.get(user__id=data['instructor_id']).user
            part.save()
        bundle.obj = ViewEvent(occ=occ)
        return bundle

    def move_event(self, bundle, requesst=None, **kwargs):
        data = bundle.body
        id_data = self._get_id_data(kwargs['pk'])
        ev = Event.objects.get(id=id_data['id'])
        occ = ev.get_occurrence(id_data['start'])

        if not occ.cancelled and data['cancelled']:
            #occ.cancel()
            pass
        bundle.obj = ViewEvent(occ=occ)
        return bundle

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
post_save.connect(update_event_resource, sender=Comment)
post_save.connect(update_event_resource, sender=Accident)
post_save.connect(update_event_resource, sender=Event)
