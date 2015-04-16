import logging
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.signals import pre_save
import django.dispatch
from django.db import models, IntegrityError
from django.middleware.transaction import transaction
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.dispatch import receiver
from django.template.defaultfilters import date as _date
from django.template.defaultfilters import time as _time
import reversion
from schedule.models import Event, Occurrence
from stables.models.event_metadata import EventMetaData
from stables.models.horse import Horse
from stables.models import CANCELED, SKIPPED, ATTENDING, RESERVED, PARTICIPATION_STATES, part_move
from stables.models.course import Course, Enroll
from stables.models.user import UserProfile

OCCURRENCE_LIST_WEEKS = 5

class ParticipationError(Exception):
    pass

recurring_change = django.dispatch.Signal(providing_args=['prev', 'new'])

logger = logging.getLogger(__name__)

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
