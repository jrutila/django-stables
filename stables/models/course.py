import datetime

from django.utils.formats import time_format
from django.db import models
from django.db.models import Q
from schedule.models import Event, Occurrence, Rule
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.template.defaultfilters import date as _date

from stables.models import *
from stables.models.common import CurrencyField, TicketType
from stables.models.user import RiderLevel, UserProfile

__author__ = 'jorutila'

class CourseManager(models.Manager):
    def get_course_occurrences(self, start, end):
        # TODO: This is common wiht ParticipationManager._get_events
        weekday = (start.isoweekday()%7)+1
        return Event.objects.exclude(end_recurring_period__lt=start).filter(
            (Q(start__week_day=weekday) & Q(rule__frequency='WEEKLY')) |
            (Q(rule__frequency__isnull=True) & Q(start__gte=start) & Q(end__lte=end)) |
            (Q(occurrence__in=Occurrence.objects.filter(start__gte=start, end__lte=end)))
        ).prefetch_related('course_set').prefetch_related('occurrence_set', 'rule').select_related().distinct()

class Course(models.Model):
    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        app_label = "stables"
        permissions = (
            ('view_participations', "Can see detailed participations"),
        )
    def __str__(self):
        try:
            ev = next(e for e in self.events.all() if e.rule != None)
            if ev:
                start = timezone.localtime(ev.start)
                return _date(start, 'D') + " " + time_format(start, "TIME_FORMAT") + " " + self.name
        except StopIteration:
            pass
        return self.name
    name = models.CharField(_('name'), max_length=500)
    events = models.ManyToManyField(Event, blank=True, null=True)

    max_participants = models.IntegerField(_('maximum participants'), default=7)
    default_participation_fee = CurrencyField(_('default participation fee'), default=0)
    ticket_type = models.ManyToManyField(TicketType, verbose_name=_('Default ticket type'), blank=True)
    allowed_levels = models.ManyToManyField(RiderLevel, verbose_name=_('Allowed rider levels'), blank=True)
    api_hide = models.BooleanField(_('Hide from api'), default=False)

    objects = CourseManager()

    #def get_next_occurrence #TODO:
    def get_next_occurrences(self, amount=1, since=timezone.now()):
        #only_active = Q(end_recurring_period__gte=since) | Q(end_recurring_period__isnull=True)
        evs = self.events.all() #.filter()
        starts = []
        for e in evs:
            if e.rule == None:
                occ = None
                try:
                    occ = next(e.occurrences_after(since))
                except StopIteration:
                    pass
                if occ:
                    starts.append(occ)
            else:
                i = 0
                for o in e.occurrences_after(since):
                    if o == None:
                        break
                    starts.append(o)
                    i = i + 1
                    if i >= amount:
                        break
        return sorted(starts, key=lambda o: o.start)[:amount]

    def addEvent(self, **event):
        event["title"] = self.name
        self.events.create(**event)

    def _curEv(self, at):
        curEv = self.events.filter(Q(
            Q(end_recurring_period__isnull=True) | Q(end_recurring_period__gte=at)
        ), rule__isnull=False)
        if (curEv): return curEv[0]
        return None

    def setRecurrentEvent(self, **event):
        event["title"] = self.name
        event["rule"] = Rule.objects.filter(frequency="WEEKLY")[0]
        curEv = self._curEv(event["start"].date())
        doAdd = True
        if (curEv):
            if curEv.start == event["start"] and curEv.end == event["end"]:
                curEv.end_recurring_period = event["end_recurring_period"]
                doAdd = False
            else:
                curEv.end_recurring_period = event["start"].date() # start of date
            curEv.save()
        if doAdd:
            self.addEvent(**event)

    def updateEventNames(self, all=False):
        if all:
            self.events.update(title=self.name)
        else:
            at = timezone.now()
            curEv = self._curEv(at)
            if curEv:
                gen = curEv.occurrences_after(at)
                try:
                    nextOcc = gen.next()
                    # Find first occurrence that is not moved
                    while (nextOcc.original_start != nextOcc.start or nextOcc.original_end != nextOcc.end):
                        nextOcc.title = self.name
                        nextOcc.save()
                        nextOcc = gen.next()

                    self.setRecurrentEvent(
                        start=nextOcc.start,
                        end=nextOcc.end,
                        end_recurring_period=curEv.end_recurring_period)
                except StopIteration:
                    pass

def get_course(self):
    return self.course_set.all()[0]

Event.course = property(get_course)

class EnrollManager(models.Manager):
    def get_query_set(self):
        return super(EnrollManager, self).get_query_set().prefetch_related('course', 'participant__user')

    def get_enrolls(self, course, occurrence=None):
        return self.filter(course=course)

class Enroll(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return str(self.course) + ": " + str(self.participant)
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

    def cancel(self):
        self.state = CANCELED
        self.save()
