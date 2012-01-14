from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from schedule.models import Calendar, Event, Rule, Occurrence
from user import UserProfile, RiderLevel, RiderInfo
from financial import CurrencyField, TicketType
from django import forms
from django.template.defaultfilters import slugify
import datetime
from django.utils.translation import ugettext, ugettext_lazy as _
from django.template.defaultfilters import date, time
from django.core.exceptions import ObjectDoesNotExist
import reversion
from django.db.models.signals import post_save
from django.dispatch import receiver

import logging

class ParticipationError(Exception):
    pass

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
    name = models.CharField(max_length=500)
    start = models.DateField()
    end = models.DateField(blank=True, null=True)
    events = models.ManyToManyField(Event, blank=True, null=True)
    creator = models.ForeignKey(User, null=True)
    created_on = models.DateTimeField(default = datetime.datetime.now)
    max_participants = models.IntegerField(default=7)
    default_participation_fee = CurrencyField(default=0.00)
    course_fee = CurrencyField(default=0.00)
    ticket_type = models.ManyToManyField(TicketType, blank=True)
    allowed_levels = models.ManyToManyField(RiderLevel, blank=True)

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
                endd = start+datetime.timedelta(days=51*7)
            occs = e.get_occurrences(
                datetime.datetime.combine(start, datetime.time(0,0)),
                datetime.datetime.combine(endd, datetime.time(23,59)))
            for c in occs:
                occurrences.append(c)
        occurrences.sort(key=lambda occ: occ.start)
        return occurrences

    def get_occurrence(self, occurrence):
        for (i, c) in enumerate(self.get_occurrences()):
            if c == occurrence:
                return (i, c)

    def get_next_occurrence(self):
        occurrences = []
        for e in self.events.all():
            occ = e.next_occurrence()
            occurrences.append(occ)
        occurrences.sort(key=lambda occ: occ.start)
        return occurrences[0]

    def full_rider(self, occurrence, nolimit=False, include_states=False):
        p_query = Participation.objects.get_participations(occurrence).order_by('last_state_change_on')
        e_query = Enroll.objects.filter(course=self).exclude(participant__in=(x.participant for x in p_query))
        e_attnd = e_query.filter(state=ATTENDING)
        p_attnd = p_query.filter(state=ATTENDING)
        all = list(p_attnd) + list(e_attnd)
        if include_states:
            all = list((y.participant, y.state) for y in sorted(all, key=lambda x: x.last_state_change_on))
        else:
            all = list(y.participant for y in sorted(all, key=lambda x: x.last_state_change_on))
        if nolimit or len(all) < self.max_participants:
            p_resvd = p_query.filter(state=RESERVED)
            e_resvd = e_query.filter(state=RESERVED)
            more = list(p_resvd) + list(e_resvd)
            if include_states:
                more = list((y.participant, y.state) for y in sorted(more, key=lambda x: x.last_state_change_on))
            else:
                more = list(y.participant for y in sorted(more, key=lambda x: x.last_state_change_on))
            all = all + more
        if not nolimit:
            all = all[:self.max_participants]
        return all

    def is_full(self, occurrence):
        p_part = Participation.objects.get_participations(occurrence).values_list('participant', flat=True)
        p_attnd = Participation.objects.get_participations(occurrence).filter(Q(state=ATTENDING) | Q(state=RESERVED)).count()
        c_attnd = Enroll.objects.filter(Q(state=ATTENDING) | Q(state=RESERVED), course=self).exclude(participant__in=p_part).count()
        return p_attnd+c_attnd >= self.max_participants

    def get_possible_states(self, rider, occurrence):
        # If this course is in the past (end date gone), can't do anything
        if occurrence.end < datetime.datetime.now():
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

    def create_participation(self, rider, occurrence, state, force=False):
        pstates = self.get_possible_states(rider, occurrence)
        parti = Participation.objects.get_participation(rider, occurrence)
        if not parti:
            parti = Participation()
            parti.participant = rider
            parti.event = occurrence.event
            parti.start = occurrence.original_start
            parti.end = occurrence.original_end

        if state in pstates or force:
            parti.state = state
            #TODO: update reversion
            #reversion.set_comment("Attending")
        elif state == ATTENDING and RESERVED in pstates:
            parti.state = RESERVED
        else:
            raise ParticipationError

        parti.save()
        return parti

    @models.permalink
    def get_absolute_url(self):
        return ('stables.views.view_course', (), { 'course_id': self.id })

ATTENDING = 0
ATTENDED = 1
SKIPPED = 2
CANCELED = 3
REJECTED = 4
RESERVED = 5
WAITFORPAY = 6
PARTICIPATION_STATES = (
    (ATTENDING, _('Attending')),
    (ATTENDED, _('Attended')),
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
class Enroll(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return str(self.course) + ": " + str(self.participant)
    course = models.ForeignKey(Course)
    participant = models.ForeignKey(UserProfile)
    state = models.IntegerField(choices=ENROLL_STATES, default=WAITFORPAY)
    last_state_change_on = models.DateTimeField(default=datetime.datetime.now())
    
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

logger = logging.getLogger(__name__)

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course

    starttime = forms.TimeField(required=False)
    endtime = forms.TimeField(required=False)

    def save(self, force_insert=False, force_update=False, commit=True):
        course = super(forms.ModelForm, self).save(commit=True)
        if self.cleaned_data['starttime'] and self.cleaned_data['endtime']:
            e = Event()
            e.start = datetime.datetime.combine(self.cleaned_data['start'], self.cleaned_data['starttime'])
            e.end = datetime.datetime.combine(self.cleaned_data['start'], self.cleaned_data['endtime'])
            e.title = self.cleaned_data['name']
            e.calendar = Calendar.objects.get(pk=1)
            e.creator = self.cleaned_data['creator']
            e.created_on = self.cleaned_data['created_on']
            e.rule = Rule.objects.get(pk=1)
            if self.cleaned_data['end']:
              e.end_recurring_period = datetime.datetime.combine(self.cleaned_data['end'], self.cleaned_data['endtime'])
            e.save()
            course.events.add(e)
        return course

    def save_m2m(self, *args, **kwargs):
        pass

class CourseParticipationActivator(models.Model):
    class Meta:
        app_label='stables'
    enroll = models.ForeignKey(Enroll)
    activate_before_hours = models.IntegerField()

    def try_activate(self):
        pass
        if self.enroll.state != ATTENDING:
            self.delete()
            return None
        p = None
        occ = self.enroll.course.get_next_occurrence()
        if occ.start-datetime.timedelta(hours=self.activate_before_hours) < datetime.datetime.now() and not Participation.objects.filter(participant=self.enroll.participant, start=occ.original_start):
          p = self.enroll.course.create_participation(self.enroll.participant, occ, self.enroll.state, force=True)
        return p

@receiver(post_save, sender=Enroll)
def handle_Enroll_save(sender, **kwargs):
    enroll = kwargs['instance']
    if enroll.state == ATTENDING and not CourseParticipationActivator.objects.filter(enroll=enroll).exists():
        # TODO: get the 24 from somewhere else
        CourseParticipationActivator.objects.create(enroll=enroll, activate_before_hours=24)

class ParticipationManager(models.Manager):
    def get_participation(self, rider, occurrence):
        parts = self.filter(participant=rider, start=occurrence.original_start, end=occurrence.original_end)
        if not parts:
            return None
        return parts[0]

    def get_participations(self, occurrence):
        return self.filter(start=occurrence.original_start, end=occurrence.original_end, ).order_by('last_state_change_on')

class Participation(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        date_format = u'l, %s' % ugettext("DATE_FORMAT")
        time_format = u'%s' % ugettext("TIME_FORMAT")
        return ugettext('%(name)s %(state)s %(event)s: %(start)s %(starttime)s - %(endtime)s') % {
            'name': self.participant,
            'state': PARTICIPATION_STATES[self.state][1],
            'event': self.event.title,
            'start': date(self.get_occurrence().start.date(), date_format),
            'starttime': time(self.get_occurrence().start.time(), time_format),
            'endtime': time(self.get_occurrence().end.time(), time_format),
        }
    def short(self):
        return ugettext('%(name)s %(state)s') % {
            'name': self.participant,
            'state': PARTICIPATION_STATES[self.state][1],
        }
    state = models.IntegerField(choices=PARTICIPATION_STATES,default=0)
    participant = models.ForeignKey(UserProfile)
    event = models.ForeignKey(Event)
    start = models.DateTimeField()
    end = models.DateTimeField()
    last_state_change_on = models.DateTimeField(default=datetime.datetime.now)
    created_on = models.DateTimeField(default=datetime.datetime.now)
    objects = ParticipationManager()

    def save(self, omitstatechange=False):
        if self.id and not omitstatechange:
            old = Participation.objects.get(pk=self.id)
            if old.state != self.state:
                self.last_state_change_on = datetime.datetime.now()
        return models.Model.save(self)

    def cancel(self):
        self.state = 3
        #TODO: update reversion
        #reversion.set_comment("Canceled")
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
        return Occurrence.objects.get(event = self.event, original_start = self.start)

#class RiderEvent(models.Model):
    #allowed_levels = models.CharField(max_length=20, choices=RIDER_LEVELS)
