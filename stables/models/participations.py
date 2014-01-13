from django.db import models
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models import Count
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from schedule.models import Event, Occurrence
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

import logging

OCCURRENCE_LIST_WEEKS = 5

class ParticipationError(Exception):
    pass

class CourseManager(models.Manager):
    def get_course_occurrences(self, start, end):
        events = Participation.objects._get_events(start, end)
        return events

class Course(models.Model):
    """
    >>> reversion.set_comment = lambda x: x
    >>> cal = Calendar()
    >>> cal.save()
    >>> rule = Rule(frequency = "WEEKLY", name = "Weekly")
    >>> rule.save()
    >>> course = Course.objects.create(name='test', start=datetime.date.today()-datetime.timedelta(days=3), end=datetime.date.today()+datetime.timedelta(days=27))
    >>> event = Event(calendar=cal,rule=rule, start=course.start+datetime.timedelta(hours=11), end=course.start+datetime.timedelta(hours=12), end_recurring_period=course.start+datetime.timedelta(days=30, hours=12))
    >>> event.save()
    >>> course.events.add(event)
    >>> course.save()
    >>> user = User(username='user',first_name='Test', last_name='Guy')
    >>> user.save()
    """
    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        app_label = "stables"
        permissions = (
            ('view_participations', "Can see detailed participations"),
        )
    def __unicode__(self):
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
                datetime.datetime.combine(start, datetime.time(0,0)),
                datetime.datetime.combine(endd, datetime.time(23,59)))
            for c in occs:
                occurrences.append(c)
        occurrences.sort(key=lambda occ: occ.start)
        return occurrences

    def get_occurrence(self, start):
        return self.get_occurrences(start=start)[0]

    def get_course_time_info(self):
        res = None
        event = self.events.filter(Q(end_recurring_period__gte=datetime.datetime.now()) | Q(end_recurring_period__isnull=True))
        if event:
            res = { 'start': event[0].start, 'end': event[0].end }
        return res

    def get_next_occurrence(self):
        occurrences = []
        for e in self.events.all():
            occ = e.next_occurrence()
            if occ:
              occurrences.append(occ)
        occurrences.sort(key=lambda occ: occ.start)
        if len(occurrences) < 1:
          return None
        return occurrences[0]

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

    def get_possible_states(self, rider, occurrence=None, ignore_date_check=False):
      if occurrence:
        # If this course is in the past (end date gone), can't do anything
        if not ignore_date_check and occurrence.end < datetime.datetime.now():
            return []

        enroll = self.enroll_set.filter(participant=rider)
        isfull = self.is_full(occurrence)
        riders = self.full_rider(occurrence)
        p = Participation.objects.get_participation(rider, occurrence)
        me = None

        # If user is attending, can cancel
        if p and p.state == ATTENDING:
            return [CANCELED]

        # If user has reserved and is in the list, can confirm or cancel
        if p and p.state == RESERVED and rider in riders:
            return [ATTENDING, CANCELED]
        elif p and p.state == RESERVED:
            return [CANCELED]

        if p and p.state == CANCELED and isfull:
            return [RESERVED]

        if not enroll:
            # If user is not enrolled and is not in the list
            if isfull and rider not in riders:
                return [RESERVED]
            elif not isfull:
                return [ATTENDING]
        else:
            enroll = enroll[0]
            if not p:
                if enroll.actual_state == ATTENDING:
                    return [CANCELED]
                elif enroll.actual_state == RESERVED:
                    if rider not in riders:
                        return [CANCELED]
                    else:
                        return [ATTENDING, CANCELED]

        if not isfull:
            return [ATTENDING]
        else:
            return [RESERVED]
      else:
        enroll = self.enroll_set.filter(participant=rider)
        isfull = self.is_full()
        c_attnd = Enroll.objects.filter(Q(state=ATTENDING) | Q(state=RESERVED), course=self)
        if enroll:
          enroll = enroll[0]
          if enroll.state == ATTENDING:
            return [CANCELED]
          full = c_attnd.order_by('last_state_change_on')[0:self.max_participants]
          if enroll.state == RESERVED:
            if enroll in full:
              return [ATTENDING, CANCELED]
            return [CANCELED]
        if isfull:
          return [RESERVED]
        return [ATTENDING]

    def attend(self, rider, occurrence):
        """
        >>> course = Course.objects.get(pk=1)
        >>> user = User.objects.filter(username='user')[0]
        >>> occ = course.get_occurrences()[1]
        >>> p = course.attend(user.get_profile(), occ)
        >>> p.state
        0
        >>> p.id > 0
        True
        >>> oc2 = course.get_occurrences()[2]
        >>> p2 = course.attend(user.get_profile(), occ)
        Traceback (most recent call last):
          File "/usr/lib/python2.7/site-packages/django/test/_doctest.py", line 1267, in __run
            compileflags, 1) in test.globs
          File "<doctest stables.models.CourseForm.Meta.model.attend[16]>", line 1, in <module>
            p2 = course.attend(user.get_profile(), occ)
          File "/home/jorutila/devel/hepokoti/stables/models.py", line 136, in attend
            raise AlreadyAttendingError()
        AlreadyAttendingError
        >>> cuser = User(username='cuser', first_name='Second', last_name='Guy')
        >>> cuser.save()
        >>> pc = course.attend(cuser.get_profile(), occ)
        >>> pc.state
        0
        >>> pc.state = 3
        >>> pc.save()
        >>> course.max_participants = 1
        >>> user2 = User(username='user2', first_name='Second', last_name='Guy')
        >>> user2.save()
        >>> p2 = course.attend(user2.get_profile(), occ)
        >>> p2.state
        5
        >>> pc = course.attend(cuser.get_profile(), oc2)
        >>> pc.state
        0
        >>> pc.state = 3
        >>> pc.save()
        >>> p2 = course.attend(user2.get_profile(), oc2)
        >>> p2.state
        0
        """
        return self.create_participation(rider, occurrence, ATTENDING)

    def get_participation(self, rider, occurrence):
        enroll = Enroll.objects.filter(participant=rider, course=self)
        parti = Participation.objects.get_participation(rider, occurrence)
        if (not enroll.exists() or enroll[0].state != ATTENDING) and not parti:
          return None
        if not parti and enroll[0].last_state_change_on > occurrence.start:
          return None
        if not parti:
            parti = Participation()
            parti.participant = rider
            parti.event = occurrence.event
            parti.start = occurrence.start
            parti.end = occurrence.end
            parti.note = ""
        return parti

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
SKIPPED = 2
CANCELED = 3
REJECTED = 4
RESERVED = 5
WAITFORPAY = 6
PARTICIPATION_STATES = (
    (ATTENDING, _('Attending')),
    (-1, 'Obsolete'),
    (SKIPPED, _('Skipped')),
    (CANCELED, _('Canceled')),
    (REJECTED, _('Rejected')),
    (RESERVED, _('Reserved')),
)
ENROLL_STATES = (
    (WAITFORPAY, _('Waiting for payment')),
    (ATTENDING, _('Attending')),
    (CANCELED, _('Canceled')),
    (REJECTED, _('Rejected')),
    (RESERVED, _('Reserved')),
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
        if occ and occ.start-datetime.timedelta(hours=self.activate_before_hours) < datetime.datetime.now() and not Participation.objects.filter(participant=self.enroll.participant, start=occ.start):
          p = Participation.objects.create_participation(self.enroll.participant, occ, self.enroll.state, force=True)
          reversion.set_comment('Automatically created by activator')
        return p

@receiver(post_save, sender=Enroll)
def handle_Enroll_save(sender, **kwargs):
    enroll = kwargs['instance']
    if enroll.state == ATTENDING and not CourseParticipationActivator.objects.filter(enroll=enroll).exists():
        # TODO: get the 24 from somewhere else
        CourseParticipationActivator.objects.create(enroll=enroll, activate_before_hours=24)

def part_move(self, course, start, end):
    # Let's get the original occurrence
    occ = course.get_occurrence(start[0])
    self.filter(event=occ.event, start=start[0], end=end[0]).update(start=start[1], end=end[1])

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
        if not parti:
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
        parts = self.filter(participant=rider, start=occurrence.start, end=occurrence.end)
        if not parts:
            return None
        return parts[0]

    def get_participations(self, occurrence):
        return self.filter(start=occurrence.start, end=occurrence.end, ).order_by('last_state_change_on')

    def get_next_participation(self, rider, start=None):
        enrolls = Enroll.objects.filter(participant=rider, state=ATTENDING)
        next_occ = None
        next_part = None
        for e in enrolls:
          n = e.course.get_next_occurrence()
          if not n:
            continue
          if not next_occ or next_occ.start > n.start:
            next_occ = n 
        parts = Participation.objects.filter(participant=rider, start__gte=datetime.datetime.now())
        for p in parts:
          n = p.event.next_occurrence()
          if not n:
            continue
          if not next_occ or next_occ.start >= n.start:
            next_occ = n 
            next_part = p
        if not next_occ:
          return None
        if next_part:
          return next_part
        part = Participation()
        part.participant = rider
        part.event = next_occ.event
        part.start = next_occ.start
        part.end = next_occ.end
        return part

    move = part_move
    cancel = part_cancel

    def _get_events(self, start, end):
        weekday = (start.isoweekday()%7)+1
        return Event.objects.exclude(end_recurring_period__lt=start).filter((Q(start__week_day=weekday) & Q(rule__frequency='WEEKLY')) | (Q(rule__frequency__isnull=True) & Q(start__gte=start) & Q(end__lte=end))).prefetch_related('course_set').prefetch_related('occurrence_set', 'rule').select_related()

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
        return ugettext('%(name)s %(state)s %(event)s: %(start)s %(starttime)s - %(endtime)s') % {
            'name': self.participant,
            'state': PARTICIPATION_STATES[self.state][1],
            'event': self.event.title,
            'start': date(occ.start.date(), date_format),
            'starttime': time(occ.start.time(), time_format),
            'endtime': time(self.get_occurrence().end.time(), time_format),
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

    def save(self, omitstatechange=False):
        if self.id and not omitstatechange:
            old = Participation.objects.get(pk=self.id)
            if old.state != self.state:
                self.last_state_change_on = datetime.datetime.now()
        sid = transaction.savepoint()
        try:
          ret = models.Model.save(self)
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

    def get_occurrence(self):
        """
        >>> cal = Calendar()
        >>> cal.save()
        >>> rule = Rule(frequency = "WEEKLY", name = "Weekly")
        >>> rule.save()
        >>> event = Event(calendar=cal,rule=rule, start=datetime.datetime(2011,1,1,11,0,0), end=datetime.datetime(2011,1,1,12,0,0))
        >>> event.rule
        <Rule: Weekly>
        >>> event.save()
        >>> fake = Event(calendar=cal,rule=rule, start=datetime.datetime(2011,1,1,11,0,0), end=datetime.datetime(2011,1,1,12,0,0))
        >>> fake.save()
        >>> occurrences = event.get_occurrences(datetime.datetime(2011,1,1), datetime.datetime(2011,1,31))
        >>> ["%s to %s" %(o.start, o.end) for o in occurrences]
        ['2011-01-01 11:00:00 to 2011-01-01 12:00:00', '2011-01-08 11:00:00 to 2011-01-08 12:00:00', '2011-01-15 11:00:00 to 2011-01-15 12:00:00', '2011-01-22 11:00:00 to 2011-01-22 12:00:00', '2011-01-29 11:00:00 to 2011-01-29 12:00:00']
        >>> p = Participation(event=event,start=datetime.datetime(2011,1,8,11,0,0), end=datetime.datetime(2011,1,8,12,0,0))
        >>> o = p.get_occurrence()
        >>> o.event
        <Event: : Saturday, Jan. 1, 2011-Saturday, Jan. 1, 2011>
        >>> o.start
        datetime.datetime(2011, 1, 8, 11, 0)
        >>> o.end
        datetime.datetime(2011, 1, 8, 12, 0)
        >>> o.move(datetime.datetime(2011, 1, 9, 15, 0), datetime.datetime(2011, 1, 9, 16, 0))
        >>> o = p.get_occurrence()
        >>> o.event
        <Event: : Saturday, Jan. 1, 2011-Saturday, Jan. 1, 2011>
        >>> o.start
        datetime.datetime(2011, 1, 9, 15, 0)
        >>> o.end
        datetime.datetime(2011, 1, 9, 16, 0)
        """
        occ = self.event.get_occurrence(self.start)
        if occ:
            return occ
        try:
          return Occurrence.objects.get(event = self.event, start = self.start)
        except ObjectDoesNotExist:
          return None

@receiver(pre_save, sender=Occurrence)
def move_participations(sender, **kwargs):
    occ = kwargs['instance']
    course = occ.event.course_set.all()[0]
    if occ.cancelled:
        Participation.objects.cancel(course, occ.start, occ.end)
    if occ.pk:
        orig = Occurrence.objects.get(pk=occ.pk)
        orig_start = orig.start
        orig_end = orig.end
    else:
        orig_start = occ.original_start
        orig_end = occ.original_end
    Participation.objects.move(course, (orig_start, occ.start), (orig_end, occ.end))
    EventMetaData.objects.move(course, (orig_start, occ.start), (orig_end, occ.end))
    InstructorParticipation.objects.move(course, (orig_start, occ.start), (orig_end, occ.end))


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
#class RiderEvent(models.Model):
    #allowed_levels = models.CharField(max_length=20, choices=RIDER_LEVELS)

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

    notes = models.TextField()
