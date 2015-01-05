from django.db.models.query import QuerySet
from tastypie.resources import ModelResource
from tastypie.resources import Resource
from stables.models import UserProfile
from stables.models import Participation
from stables.models import InstructorParticipation
from stables.models import InstructorInfo
from stables.models import Horse
from stables.models import Transaction
from stables.models import ATTENDING, CANCELED, SKIPPED, RESERVED
from schedule.models import Event
from schedule.models import Calendar
from schedule.models import Occurrence
from stables.models import EventMetaData
from stables.models import Accident
from stables.models import Ticket
from stables.models import TicketType
from stables.models import pay_participation
from stables.models import Enroll
from stables.models import Course
from stables.models import financial
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.cache import SimpleCache
from tastypie.authorization import Authorization
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField
from tastypie.http import HttpBadRequest
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.utils import trailing_slash
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from django.db.models.signals import post_save
from django.conf.urls import url

from django.contrib.comments import Comment
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

import datetime
from django.utils import timezone
from dateutil import parser

from django.utils.translation import ugettext as _
from django.db.models import Q
import operator
import json
from tastypie.authentication import SessionAuthentication

import logging
from stables.utils import getPaymentLink

logger = logging.getLogger(__name__)

class ParticipationPermissionAuthentication(SessionAuthentication):
    def is_authenticated(self, request, **kwargs):
        return request.user.has_perm('stables.change_participation')

class UserResource(ModelResource):
    class Meta:
        queryset = UserProfile.objects.active()
        cache = SimpleCache(timeout=30*60)
        authentication = ParticipationPermissionAuthentication()
    name = fields.CharField()

    def dehydrate_name(self, bundle):
        return bundle.obj.user.first_name + " " + bundle.obj.user.last_name

class HorseQuerySet(QuerySet):
    def filter(self, *args, **kwargs):
        return super(HorseQuerySet, self).complex_filter(Q(Q(**kwargs) | Q(last_usage_date__isnull=True)))

class HorseResource(ModelResource):
    class Meta:
        queryset = HorseQuerySet(Horse, using=Horse.objects._db)
        cache = SimpleCache(timeout=30*60)
        authentication = ParticipationPermissionAuthentication()
        filtering = {
            'last_usage_date': ['gte'],
        }
    name = fields.CharField(attribute="name")
    day_limit = fields.IntegerField(attribute="day_limit", null=True)
    last_usage_date = fields.DateField(attribute="last_usage_date", null=True)

class EventMetaDataResource(ModelResource):
    class Meta:
        queryset  = EventMetaData.objects.all()
        object_class = EventMetaData
        authorization= Authorization()
        always_return_data = True
        authentication = ParticipationPermissionAuthentication()
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
        authentication = ParticipationPermissionAuthentication()

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj
        return { 'pk': bundle_or_obj.id }

    def hydrate_content_object(self, bundle):
        obj = bundle.data['content_object']
        # TODO: There has to be better way!
        if isinstance(obj, dict):
            if 'id' not in obj:
                obj['event'] = int(obj['event'].split('/')[-2])
                obj['event'] = Event.objects.get(pk=obj['event'])
            else:
                pk = obj['id']
                obj = { 'id': pk }
        else:
            pk = int(obj.split('/')[-2])
            obj = { 'id': pk }
        bundle.data['content_object'] = EventMetaData.objects.get_or_create(**obj)[0]
        return bundle

    def obj_create(self, bundle, **kwargs):
        kwargs['site'] = Site.objects.get_current()
        return super(CommentResource, self).obj_create(bundle, **kwargs)

from decimal import Decimal
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

class ApiList(list):
    def all(self):
        return self

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
            self.course = course.get_absolute_url()
        if metadata:
            self.metadata = metadata
        if last_comment:
            self.last_comment = last_comment.comment
            self.last_comment_date = last_comment.submit_date
            self.last_comment_user = last_comment.user_name

class EnrollResource(ModelResource):
    class Meta:
        resource_name = 'enroll'
        object_class = Enroll
        list_allowed_methods = ['post', 'put']
        authentication = ParticipationPermissionAuthentication()

    event = fields.IntegerField()

    def obj_create(self, bundle, request=None, **kwargs):
        part = UserProfile.objects.get(pk=bundle.data['rider'])
        event = Event.objects.get(pk=bundle.data['event'])
        enroll = Enroll.objects.get_or_create(course=event.course_set.all()[0], participant=part)[0]
        enroll.state = 0
        enroll.last_state_change_on = datetime.datetime.now()
        enroll.save()

    def obj_update(self, bundle, request=None, **kwargs):
        enroll = Enroll.objects.get(pk=kwargs['pk'])
        enroll.state = bundle.data['state']
        enroll.last_state_change_on = datetime.datetime.now()
        enroll.save()

class ViewFinance:
    def __init__(self, part=None):
        self.id = 0
        if part:
            self.id = part.id
            saldo, ticket, value = part.get_saldo()
            if value:
                value = value.quantize(Decimal('0.01'))
            self.tickets = {}
            self.method = ""

            unused = part.participant.rider.unused_tickets
            for u in unused:
                if (not ticket) or (ticket.type != u.type):
                    self.tickets[u.type.id] = u.type.name
            self.participation_url = part.get_absolute_url()
            self.finance_hint = str(value)
            if saldo < Decimal('0.00'):
                self.finance_hint = str(saldo)
            else:
                try:
                    method = part.get_pay_transaction().method or _('Cash')
                    method = method.title()
                except IndexError:
                    method = _('Cash')
                self.finance_hint = method + " " + str(value)

            if ticket:
                if value:
                    self.amount = value
                self.method = ticket.type.id
                self.finance_hint = unicode(ticket)
            else:
                if value == None or saldo < Decimal('0.00'):
                    self.amount = value

            if part.state != ATTENDING and part.state != SKIPPED:
                self.tickets = {}
                from stables.models import PARTICIPATION_STATES
                self.finance_hint = PARTICIPATION_STATES[part.state][1]

            self.linkmethods = []
            if part.participant.phone_number:
                self.linkmethods.append('mobile')
            if part.participant.user.email:
                self.linkmethods.append('email')

class FinanceResource(Resource):
    class Meta:
        resource_name = "financials"
        always_return_data = True
        object_class = ViewFinance
        authentication = ParticipationPermissionAuthentication()

    id = fields.IntegerField(attribute='id')
    finance_hint = fields.CharField(attribute='finance_hint', null=True)
    participation_url = fields.CharField(attribute='participation_url')

    amount = fields.CharField(attribute='amount', null=True)
    method = fields.CharField(attribute='method')

    tickets = fields.DictField(attribute='tickets', null=True)
    linkmethods = fields.ListField(attribute='linkmethods')

    def obj_get(self, bundle, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        return ViewFinance(part)

    def obj_update(self, bundle, request=None, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        amount = bundle.data['amount']
        method = bundle.data['method']
        try:
            pay_participation(part, ticket=TicketType.objects.get(pk=int(method)))
        except ValueError:
            pay_participation(part, value = Decimal(amount) if amount != "" else None, method=method.lower())
        bundle.obj = ViewFinance(part)
        return bundle

class PaymentLinkObject():
    pass

class PaymentLinkResource(Resource):
    participation_id = fields.IntegerField(attribute="participation_id")
    method = fields.CharField(attribute="method")
    url = fields.CharField(attribute="url")
    extra = fields.CharField(attribute="extra", null=True)

    class Meta:
        resource_name = 'paymentlink'
        authentication = ParticipationPermissionAuthentication()
        object_class = PaymentLinkObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.participation_id
        else:
            kwargs['pk'] = bundle_or_obj.participation_id
        return kwargs

    def obj_create(self, bundle, **kwargs):
        bundle.obj = PaymentLinkObject()
        bundle.obj.method = bundle.data['method']
        bundle.obj.participation_id = bundle.data['participation_id']
        shortUrl = getPaymentLink(bundle.obj.participation_id)
        url = bundle.request.build_absolute_uri(shortUrl)
        bundle.obj.url = url
        #TODO: Change to use settings implementations!
        part = Participation.objects.get(pk=bundle.obj.participation_id)
        if (bundle.obj.method == 'email'):
            message = 'Go pay your participation %s at url: %s' % (part, url)
            from django.core.mail import send_mail
            if ('extra' in bundle.data):
                part.participant.user.email = bundle.data['extra']
                part.participant.user.save()
            addr = part.participant.user.email
            if addr:
                send_mail('Subject', message, 'noreply@stables.fi', [addr])
        elif (bundle.obj.method == "mobile"):
            import django_settings
            message = u'Go pay your participation %s using (%s)' % (part, url) #django_settings.get('part_pay_info'))
            from django_twilio.client import twilio_client
            if ('extra' in bundle.data):
                part.participant.phone_number = bundle.data['extra']
                part.participant.save()
            nmbr = part.participant.phone_number
            msg = twilio_client.messages.create(
                body=message,
                to=settings.TEST_SMS or nmbr,
                from_='+358 45 73963377'
            )
            bundle.obj.extra = msg.sid
        return bundle

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
                # TODO: Implement new user adding logic!
                raise ImmediateHttpResponse(HttpBadRequest("Given user does not exist"))
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
        list_allowed_methods = ['get', 'post', 'put']
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
post_save.connect(enroll_update_cache_clear, sender=Enroll)
