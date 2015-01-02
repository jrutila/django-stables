from django.db import models
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models import Count
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
import django_settings
from schedule.models import Event, Occurrence, Rule
from user import UserProfile, RiderLevel
from financial import CurrencyField, TicketType
import datetime
from django.utils.translation import ugettext, ugettext_lazy as _
from django.template.defaultfilters import date, time
from django.core.exceptions import ObjectDoesNotExist
import reversion
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from horse import Horse
import django.dispatch
from django.utils import timezone
from django.template.defaultfilters import date as _date
from django.template.defaultfilters import time as _time

import logging

OCCURRENCE_LIST_WEEKS = 5

class ParticipationError(Exception):
    pass

class CourseManager(models.Manager):
    def get_course_occurrences(self, start, end):
        events = Participation.objects._get_events(start, end)
        return events

recurring_change = django.dispatch.Signal(providing_args=['prev', 'new'])

class Course(models.Model):
    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        app_label = "stables"
        permissions = (
            ('view_participations', "Can see detailed participations"),
        )
    def __unicode__(self):
        lastEvent = self._getLastEvent()
        if lastEvent:
            return "%s %s" % (_date(lastEvent.start, 'D H:i'), self.name)
        return self.name
    name = models.CharField(_('name'), max_length=500)
    start = models.DateField(_('start'))
    end = models.DateField(_('end'), blank=True, null=True)
    events = models.ManyToManyField(Event, blank=True, null=True)
    creator = models.ForeignKey(User, null=True)
    created_on = models.DateTimeField(default = datetime.datetime.now)
    max_participants = models.IntegerField(_('maximum participants'), default=7)
    default_participation_fee = CurrencyField(_('default participation fee'), default=0)
    course_fee = CurrencyField(default=0)
    ticket_type = models.ManyToManyField(TicketType, verbose_name=_('Default ticket type'), blank=True)
    allowed_levels = models.ManyToManyField(RiderLevel, verbose_name=_('Allowed rider levels'), blank=True)

    objects = CourseManager()
    
    def save(self, **kwargs):
        since = kwargs.get('since', timezone.now())
        le = self._getLastEvent()
        starttime = kwargs.get('starttime', timezone.localtime(le.start).time() if le else None)
        endtime = kwargs.get('endtime', timezone.localtime(le.end).time() if le else None)
        hasNameChange = le and self.name != le.title
        hasTimeChange = 'starttime' in kwargs and 'endtime' in kwargs and le and (
             timezone.localtime(le.start).time() != kwargs['starttime'] or
             timezone.localtime(le.end).time() != kwargs['endtime'])
        if hasNameChange or hasTimeChange:
            if self.id:
                last_event, last_occ = self._endLastEvent(since)
                if last_occ:
                    ev = Event()
                    self._updateEvent(ev, starttime, endtime, last_occ.start+datetime.timedelta(days=7), self.end)
                    ev.save()
                    self.events.add(ev)
                    if last_event:
                        last_event.save()
                        recurring_change.send(sender=Course, prev=last_event, new=ev)
                else:
                    ev = self.events.latest('start')
                    self._updateEvent(ev, starttime, endtime, last_event.start.date(), self.end)
                    ev.save()
            super(Course, self).save()
        else:
            ev = None
            if not self.id and starttime and endtime:
                ev = Event()
                self._updateEvent(ev, starttime, endtime, self.start, self.end)
                ev.save()
            elif self.id and self.end:
                last_event, last_occ = self._endLastEvent(self.end+datetime.timedelta(days=1))
                if last_event: last_event.save()
            super(Course, self).save()
            if ev: self.events.add(ev)

    def _updateEvent(self, ev, starttime, endtime, start, end=None):
        ev.title = self.name
        ev.start = timezone.get_current_timezone().localize(datetime.datetime.combine(start, starttime))
        ev.end = timezone.get_current_timezone().localize(datetime.datetime.combine(start, endtime))
        ev.rule = Rule.objects.get(name="Weekly")
        if end:
            ev.end_recurring_period = timezone.get_current_timezone().localize(datetime.datetime.combine(end, endtime))

    def _getLastEvent(self):
        if hasattr(self, '__lastEvent'):
            return self.__lastEvent
        self.__lastEvent = None
        if self.id and self.events.filter(rule__isnull=False).count() > 0:
            self.__lastEvent = self.events.filter(rule__isnull=False).order_by('-start')[0]
        return self.__lastEvent

    lastEvent = property(_getLastEvent)

    def _endLastEvent(self, since):
        last_event = self._getLastEvent()
        if type(since) is datetime.date:
            since = datetime.datetime.combine(since, datetime.time())
        if timezone.is_naive(since):
            since = timezone.get_current_timezone().localize(since)
        if last_event:
            last_occ = last_event.get_occurrences(
                      timezone.localtime(since-datetime.timedelta(days=7)),
                      timezone.localtime(since))
            if last_occ:
                last_occ = last_occ[0]
                last_event.end_recurring_period = last_occ.end
            else:
                last_occ = None
            return last_event,last_occ
        return None, None

    def get_occurrences(self, delta=None, start=None):
        if not start:
          start = self.start
        occurrences = []
        # TODO: get 365 from somewhere else than 52*7
        for e in self.events.all():
            if delta:
                endd = start+delta
            else:
                endd = self.end
            if endd == None:
                endd = start+datetime.timedelta(days=OCCURRENCE_LIST_WEEKS*7)
            occs = e.get_occurrences(
                timezone.make_aware(datetime.datetime.combine(start, datetime.time(0,0)), timezone.get_current_timezone()),
                timezone.make_aware(datetime.datetime.combine(endd, datetime.time(23,59)), timezone.get_current_timezone()))
            for c in occs:
                occurrences.append(c)
        occurrences.sort(key=lambda occ: occ.start)
        return occurrences

    # Obsolete
    def get_occurrence(self, start):
        return self.get_occurrences(start=start)[0]

    def get_next_occurrence_after(self, start):
        nexoc = None
        for e in self.events.all():
            en = next(e.occurrences_after(start), None)
            if en:
                if not nexoc:
                    nexoc = en
                if en.start < nexoc.start:
                    nexoc = en

        return nexoc

    def get_course_time_info(self):
        res = None
        event = self.events.filter(Q(end_recurring_period__gte=datetime.datetime.now()) | Q(end_recurring_period__isnull=True))
        if event:
            res = { 'start': event[0].start, 'end': event[0].end }
        return res

    def get_next_occurrences(self, limit):
        occurrences = []
        for e in self.events.all():
            it = e.occurrences_after(timezone.localtime(timezone.now()))
            for i in range(0, limit):
                occ = next(it, None)
                if occ:
                    occurrences.append(occ)
        occurrences.sort(key=lambda occ: occ.start)
        if len(occurrences) < 1:
            return None
        return occurrences[:limit]

    def get_next_occurrence(self):
        nxt = self.get_next_occurrences(1)
        if nxt:
            return nxt[0]
        return None

    def full_rider(self, occurrence, nolimit=False, include_statenames=False):
        p_query = Participation.objects.get_participations(occurrence).order_by('last_state_change_on')
        e_query = Enroll.objects.filter(course=self).exclude(participant__in=(x.participant for x in p_query))
        e_attnd = e_query.filter(state=ATTENDING)
        p_attnd = p_query.filter(state=ATTENDING)
        all = list(p_attnd) + list(e_attnd)
        if include_statenames:
            all = list((y.participant, PARTICIPATION_STATES[y.state][1]) for y in sorted(all, key=lambda x: x.last_state_change_on))
        else:
            all = list(y.participant for y in sorted(all, key=lambda x: x.last_state_change_on))
        if nolimit or len(all) < self.max_participants:
            p_resvd = p_query.filter(state=RESERVED)
            e_resvd = e_query.filter(state=RESERVED)
            more = list(p_resvd) + list(e_resvd)
            if include_statenames:
                more = list((y.participant, PARTICIPATION_STATES[y.state][1]) for y in sorted(more, key=lambda x: x.last_state_change_on))
            else:
                more = list(y.participant for y in sorted(more, key=lambda x: x.last_state_change_on))
            all = all + more
        if not nolimit:
            all = all[:self.max_participants]
        return all

    def is_full(self, occurrence=None):
      if occurrence:
        p_part = Participation.objects.get_participations(occurrence).values_list('participant', flat=True)
        p_attnd = Participation.objects.get_participations(occurrence).filter(Q(state=ATTENDING) | Q(state=RESERVED)).count()
        c_attnd = Enroll.objects.filter(Q(state=ATTENDING) | Q(state=RESERVED), course=self).exclude(participant__in=p_part).count()
        return p_attnd+c_attnd >= self.max_participants
      else:
        c_attnd = Enroll.objects.filter(Q(state=ATTENDING) | Q(state=RESERVED), course=self)
        return c_attnd.count() >= self.max_participants

    def get_attending_amount(self, occurrence=None):
      if occurrence:
        p_part = Participation.objects.get_participations(occurrence).values_list('participant', flat=True)
        p_attnd = Participation.objects.get_participations(occurrence).filter(Q(state=ATTENDING) | Q(state=RESERVED)).count()
        c_attnd = Enroll.objects.filter(Q(state=ATTENDING) | Q(state=RESERVED), course=self).exclude(participant__in=p_part).count()
        return p_attnd+c_attnd
      else:
        return Enroll.objects.filter(Q(state=ATTENDING), course=self).count()

    def can_attend(self, occurrence, rider):
        p_part = Participation.objects.get_participations(occurrence).values_list('participant', flat=True)
        p_attnd = Participation.objects.get_participations(occurrence).filter(Q(state=ATTENDING)).count()
        c_attnd = Enroll.objects.filter(Q(state=ATTENDING), course=self).exclude(participant__in=p_part).count()
        if (p_attnd + c_attnd >= self.max_participants):
            return False
        freespots = self.max_participants - p_attnd - c_attnd;
        part_q = Participation.objects.filter(
            Q(state=RESERVED),
            event=occurrence.event,
            start=occurrence.start, end=occurrence.end).order_by("last_state_change_on")
        part = part_q[:freespots]
        enroll = Enroll.objects.filter(Q(state=RESERVED), course=self).exclude(participant__in=p_part).exclude(participant__in=part)
        if not part and not enroll: return True
        if part and part_q.order_by("last_state_change_on")[0].participant == rider:
            return True
        if not part and enroll.order_by("last_state_change_on")[0].participant == rider:
            return True
        return False

    def attend(self, rider, occurrence):
        return Participation.objects.create_participation(rider, occurrence, ATTENDING)

    def get_participation(self, rider, occurrence):
        return Participation.objects.get_participation(rider, occurrence)

    def enroll(self, rider):
        (enroll, created) = Enroll.objects.get_or_create(participant=rider, course=self)
        estates = self.get_possible_states(rider)
        if ATTENDING in estates or enroll.state == ATTENDING:
          enroll.state = ATTENDING
        else:
          enroll.state = RESERVED
        enroll.save()
        return enroll

    @models.permalink
    def get_absolute_url(self):
        return ('view_course', (), { 'pk': self.id })

ATTENDING = 0
RESERVED = 1
SKIPPED = 2
CANCELED = 3
REJECTED = 4
WAITFORPAY = 6
PARTICIPATION_STATES = (
    (ATTENDING, ugettext('Attending')),
    (RESERVED, ugettext('Reserved')),
    (SKIPPED, ugettext('Skipped')),
    (CANCELED, ugettext('Canceled')),
    (REJECTED, ugettext('Rejected')),
)
ENROLL_STATES = (
    (WAITFORPAY, ugettext('Waiting for payment')),
    (ATTENDING, ugettext('Attending')),
    (CANCELED, ugettext('Canceled')),
    (REJECTED, ugettext('Rejected')),
    (RESERVED, ugettext('Reserved')),
)

class EnrollManager(models.Manager):
    def get_query_set(self):
        return super(EnrollManager, self).get_query_set().prefetch_related('course', 'participant__user')

    def get_enrolls(self, course, occurrence=None):
        return self.filter(course=course)

class Enroll(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return unicode(self.course) + ": " + unicode(self.participant)
    def short(self):
        return ugettext('%(name)s %(state)s') % {
            'name': self.participant,
            'state': PARTICIPATION_STATES[self.state][1],
        }
    course = models.ForeignKey(Course)
    participant = models.ForeignKey(UserProfile)
    state = models.IntegerField(choices=ENROLL_STATES, default=WAITFORPAY)
    last_state_change_on = models.DateTimeField(default=datetime.datetime.now())

    objects = EnrollManager()
    
    def _get_actual_state(self):
        if self.state == WAITFORPAY:
            type = ContentType.objects.get_for_model(self)
            from django.db.models import Sum
            from financial import Transaction
            sum = Transaction.objects.filter(object_id=self.id, content_type=type).aggregate(Sum('amount'))['amount__sum']
            if sum >= 0:
                return ATTENDING
        return self.state
    actual_state = property(_get_actual_state)

    def cancel(self):
      self.state = CANCELED
      self.save()

logger = logging.getLogger(__name__)


class CourseParticipationActivator(models.Model):
    class Meta:
        app_label='stables'
    enroll = models.ForeignKey(Enroll)
    activate_before_hours = models.IntegerField()

    def try_activate(self):
        if self.enroll.state != ATTENDING:
            self.delete()
            return None
        p = None
        occ = self.enroll.course.get_next_occurrence()
        if occ and occ.start-datetime.timedelta(hours=self.activate_before_hours) < timezone.now() and not Participation.objects.filter(participant=self.enroll.participant, start=occ.start):
          p = Participation.objects.create_participation(self.enroll.participant, occ, self.enroll.state, force=True)
          reversion.set_comment('Automatically created by activator')
        return p

@receiver(post_save, sender=Enroll)
def handle_Enroll_save(sender, **kwargs):
    enroll = kwargs['instance']
    if enroll.state == ATTENDING and not CourseParticipationActivator.objects.filter(enroll=enroll).exists():
        # TODO: get the 24 from somewhere else
        CourseParticipationActivator.objects.create(enroll=enroll, activate_before_hours=24)

def part_move(self, curr, prev):
    self.filter(event=prev.event, start=prev.start, end=prev.end).update(start=curr.start, end=curr.end)

def part_cancel(self, course, start, end):
    occ = course.get_occurrence(start)
    for p in self.filter(event=occ.event, start=start, end=end).exclude(state=CANCELED):
        p.state=CANCELED
        p.save()

class ParticipationManager(models.Manager):
    def create_participation(self, rider, occurrence, state, force=False):
        if occurrence.cancelled:
            raise ParticipationError("Cannot create participation on cancelled occurrence")
        # TODO: check out the possible states when user can attend himself
        pstates = [ATTENDING, CANCELED, SKIPPED] #self.get_possible_states(rider, occurrence)
        parti = Participation.objects.get_participation(rider, occurrence)

        #TODO: To common function with get_participation
        if not parti and force:
            parti = Participation()
            parti.participant = rider
            parti.event = occurrence.event
            parti.start = occurrence.start
            parti.end = occurrence.end
            parti.note = ""

        if state in pstates or force:
            reversion.set_comment("State change")
            parti.state = state
            if state not in pstates:
              reversion.set_comment("Forced state change")
        elif state == ATTENDING and RESERVED in pstates:
            parti.state = RESERVED
            reversion.set_comment("Automatically reserved")
        else:
            raise ParticipationError

        if not parti.pk:
            reversion.set_comment('Created participation')

        parti.save()
        return parti

    def get_participation(self, rider, occurrence):
        course = occurrence.event.course_set.all()
        if course:
            course = course[0]
        enroll = Enroll.objects.filter(participant=rider, course=course)
        parts = self.filter(participant=rider,
                            event=occurrence.event,
                            start=occurrence.start,
                            end=occurrence.end)
        if not parts:
            parti = Participation()
            parti.participant = rider
            parti.event = occurrence.event
            parti.start = occurrence.start
            parti.end = occurrence.end
            parti.note = ""
        else:
            parti = parts[0]
        if (not enroll.exists() or enroll[0].state != ATTENDING) and not parts:
            parti.state = CANCELED
            if (enroll.exists() and enroll[0].state == RESERVED):
                parti.state = RESERVED
        if not parts and enroll and enroll[0].last_state_change_on > occurrence.start:
            parti.state = CANCELED
        return parti

    def get_participations(self, occurrence):
        return self.filter(start=occurrence.start, end=occurrence.end, ).order_by('last_state_change_on')

    def get_next_participation(self, rider, start=None, limit=3):
        enrolls = list(Enroll.objects.filter(participant=rider, state=ATTENDING).prefetch_related('course', 'course__events', 'course__events__rule', 'course__events__occurrence_set'))
        next_part = []
        parts = list(Participation.objects.filter(participant=rider, start__gte=datetime.datetime.now()).select_related())
        next_part.extend(parts)
        for e in enrolls:
            n = e.course.get_next_occurrences(limit)
            if not n:
                continue
            for occ in n:
                part = self.get_participation(rider, occ)
                if not any(part == p for p in parts):
                    next_part.append(part)
        next_part.sort(key=lambda p: p.start)
        return next_part

    move = part_move
    cancel = part_cancel

    def _get_events(self, start, end):
        weekday = (start.isoweekday()%7)+1
        return Event.objects.exclude(end_recurring_period__lt=start).filter(
            (Q(start__week_day=weekday) & Q(rule__frequency='WEEKLY')) |
            (Q(rule__frequency__isnull=True) & Q(start__gte=start) & Q(end__lte=end)) |
            (Q(occurrence__in=Occurrence.objects.filter(start__gte=start, end__lte=end)))
            ).prefetch_related('course_set').prefetch_related('occurrence_set', 'rule').select_related().distinct()

    def generate_warnings(self, start, end):
        return { }

    def generate_participations(self, start, end):
        events = self._get_events(start, end)
        events = list(events)
        courses = Course.objects.filter(events__in=events).select_related()
        enrolls = list(Enroll.objects.filter(course__in=courses).exclude(state=CANCELED).select_related())
        parts = list(Participation.objects.filter(event__in=events, start__gte=start, end__lte=end).prefetch_related('event', 'participant__user').select_related())
        ret = {}
        partid_list = set()
        for event in events:
            crs = event.course_set.all()
            if crs:
                crs = crs[0]
            for occ in event.get_occurrences(start, end):
              occ_parts = [ p for p in parts if p.start == occ.start and p.end == occ.end and p.event == event ]
              for p in occ_parts:
                  enroll = [ e for e in enrolls if e.course == crs and e.participant == p.participant]
                  if len(enroll) == 1:
                      setattr(p, 'enroll', enroll[0])
              part_ids = [ p.participant.id for p in occ_parts ]

              for e in [ e for e in enrolls if e.course == crs and e.last_state_change_on <= occ.start and e.participant.id not in part_ids ]:
                p = Participation()
                p.participant = e.participant
                p.event = occ.event
                p.start = occ.start
                p.end = occ.end
                p.note = ""
                p.enroll = e
                occ_parts.append(p)
              ret[occ] = (crs if crs else None, [ p for p in occ_parts ])
              partid_list = partid_list | set([p.id for p in occ_parts])
        return (partid_list, ret)

class Participation(models.Model):
    class Meta:
        app_label = 'stables'
        unique_together = ('participant', 'event', 'start', 'end')
    def __unicode__(self):
        date_format = u'%s' % ugettext("DATE_FORMAT")
        time_format = u'%s' % ugettext("TIME_FORMAT")
        occ = self.get_occurrence()
        if not occ:
          return ugettext('%(name)s %(state)s No Occurrence')
        start = timezone.localtime(occ.start)
        end = timezone.localtime(occ.end)
        return ugettext('%(name)s %(state)s %(event)s: %(start)s %(starttime)s - %(endtime)s') % {
            'name': self.participant,
            'state': PARTICIPATION_STATES[self.state][1],
            'event': self.event.title,
            'start': _date(start.date(), 'SHORT_DATE_FORMAT'),
            'starttime': _time(start.time(), time_format),
            'endtime': _time(end.time(), time_format)
        }
    def short(self):
        return ugettext('%(name)s %(state)s') % {
            'name': self.participant,
            'state': PARTICIPATION_STATES[self.state][1],
        }
    def get_absolute_url(self):
        return reverse('view_participation', kwargs={'pk': self.id })
    state = models.IntegerField(choices=PARTICIPATION_STATES,default=0)
    participant = models.ForeignKey(UserProfile)
    note = models.TextField(blank=True)
    event = models.ForeignKey(Event)
    start = models.DateTimeField()
    end = models.DateTimeField()
    last_state_change_on = models.DateTimeField(default=datetime.datetime.now)
    created_on = models.DateTimeField(default=datetime.datetime.now)
    objects = ParticipationManager()

    horse = models.ForeignKey(Horse, null=True, blank=True)

    def save(self, omitstatechange=False, **kwargs):
        if self.id and not omitstatechange:
            old = Participation.objects.get(pk=self.id)
            if old.state != self.state:
                self.last_state_change_on = datetime.datetime.now()
        sid = transaction.savepoint()
        try:
          ret = models.Model.save(self, **kwargs)
          transaction.savepoint_commit(sid)
          return ret
        except IntegrityError:
          transaction.savepoint_rollback(sid)
          actual = Participation.objects.get(participant=self.participant, event=self.event, start=self.start, end=self.end)
          actual.horse = self.horse
          actual.note = self.note
          if actual.state != self.state:
            actual.last_state_change_on = datetime.datetime.now()
          actual.state = self.state
          return actual.save()

    def cancel(self):
        self.state = 3
        reversion.set_comment("Canceled")
        self.save()

    def attend(self):
        if ATTENDING in self.get_possible_states():
            self.state = ATTENDING
        elif RESERVED in self.get_possible_states():
            self.state = RESERVED
        else:
            raise AttributeError
        reversion.set_comment("Attending")
        self.save()

    def move(self, occ):
        self.event = occ.event
        self.start = occ.start
        self.end = occ.end
        reversion.set_comment("Moved")
        self.save()

    def get_possible_states(self):
        course = self.event.course_set
        course = course.all()[0] if course.exists() else None

        # No possible states for old occurrences
        if self.end < timezone.now():
            return []

        # If user is attending, can cancel
        if self.state == ATTENDING:
            return [CANCELED]

        if self.state == CANCELED:
            if course and not course.can_attend(self.get_occurrence(), self.participant):
                return [RESERVED]
            return [ATTENDING]

        if self.state == RESERVED:
            if course and not course.can_attend(self.get_occurrence(), self.participant):
                return [CANCELED]
            return [ATTENDING, CANCELED]

    def get_occurrence(self):
        occ = self.event.get_occurrence(timezone.get_current_timezone().normalize(self.start))
        if occ:
            return occ
        try:
          return Occurrence.objects.get(event = self.event, start = self.start)
        except ObjectDoesNotExist:
          return None

@receiver(recurring_change, sender=Course)
def event_changes(sender, **kwargs):
    prev = kwargs['prev']
    new = kwargs['new']
    for p in Participation.objects.filter(event=prev, start__gt=prev.end_recurring_period):
        new_occ = new.get_occurrences(
            datetime.datetime.combine(p.start.date(), datetime.time(0)).replace(tzinfo=timezone.get_current_timezone())
          , datetime.datetime.combine(p.start.date(), datetime.time(23,59)).replace(tzinfo=timezone.get_current_timezone()))
        p.move(new_occ[0])

@receiver(pre_save, sender=Occurrence)
def move_participations(sender, instance, **kwargs):
    curr = instance
    if curr.cancelled:
        course = curr.event.course_set.all()[0]
        Participation.objects.cancel(course, curr.start, curr.end)
    orig = Occurrence(event=curr.event)
    if curr.pk:
        orig = Occurrence.objects.get(pk=curr.pk)
    else:
        orig.start = curr.original_start
        orig.end = curr.original_end
    Participation.objects.move(curr, orig)
    EventMetaData.objects.move(curr, orig)
    InstructorParticipation.objects.move(curr, orig)


class InstructorParticipationManager(models.Manager):
    def get_participations(self, start, end):
        events = Event.objects.filter((Q(rule__frequency='WEEKLY') & (Q(end_recurring_period__gte=start) | Q(end_recurring_period__isnull=True))) | (Q(rule__isnull=True) & Q(start__gte=start) & Q(end__lte=end)) | (Q(occurrence__start__gte=start) & Q(occurrence__end__lte=end))).select_related('rule').prefetch_related('course_set')
        ret = {}
        for event in events:
            if event.course_set.count() == 0:
              continue
            for occ in event.get_occurrences(start, end):
                ret[occ] = (event.course_set.all()[0], list(InstructorParticipation.objects.filter(event=event, start=occ.start, end=occ.end)))

        return ret

    move = part_move
    cancel = part_cancel

class InstructorParticipation(models.Model):
    class Meta:
      app_label = 'stables'
    def __unicode__(self):
      return ugettext('%(firstname)s %(lastname)s') % { 'firstname': self.instructor.user.first_name, 'lastname': self.instructor.user.last_name }
    instructor = models.ForeignKey(UserProfile)
    event = models.ForeignKey(Event)
    start = models.DateTimeField()
    end = models.DateTimeField()
    objects = InstructorParticipationManager()

class EventMetaDataManager(models.Manager):
    def get_metadatas(self, start, end):
        events = Event.objects.filter((Q(rule__frequency='WEEKLY') & (Q(end_recurring_period__gte=start) | Q(end_recurring_period__isnull=True))) | (Q(rule__isnull=True) & Q(start__gte=start) & Q(end__lte=end)) | (Q(occurrence__start__gte=start) & Q(occurrence__end__lte=end))).select_related('rule').prefetch_related('course_set')
        ret = {}
        for event in events:
            if event.course_set.count() == 0:
              continue
            for occ in event.get_occurrences(start, end):
                ret[occ] = (event.course_set.all()[0], list(EventMetaData.objects.filter(event=event, start=occ.start, end=occ.end)))

        return ret

    move = part_move

class EventMetaData(models.Model):
    class Meta:
        app_label = 'stables'
    objects = EventMetaDataManager()

    event = models.ForeignKey(Event)
    start = models.DateTimeField()
    end = models.DateTimeField()

    max_participants = models.IntegerField(_('maximum participants'), blank=True, null=True) #, default=django_settings.get("default_max_participants", default=7))
    default_participation_fee = CurrencyField(_('default participation fee'), blank=True, null=True)#, default=django_settings.get("default_participation_fee", default=0.00))
