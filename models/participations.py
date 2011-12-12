from django.db import models
from django.contrib.auth.models import User
from schedule.models import Calendar, Event, Rule, Occurrence
from user import UserProfile
from financial import CurrencyField, TicketType
from django import forms
from django.template.defaultfilters import slugify
import datetime
from django.utils.translation import ugettext, ugettext_lazy as _
from django.template.defaultfilters import date, time
from django.core.exceptions import ObjectDoesNotExist
import reversion

import logging

class AlreadyAttendingError(Exception):
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
    end = models.DateField()
    events = models.ManyToManyField(Event, blank=True, null=True)
    creator = models.ForeignKey(User, null = True)
    created_on = models.DateTimeField(default = datetime.datetime.now)
    max_participants = models.IntegerField(default=7)
    default_participation_fee = CurrencyField(default=0.00)
    ticket_type = models.ManyToManyField(TicketType)

    def get_occurrences(self):
        occurrences = []
        for e in self.events.all():
            occs = e.get_occurrences(
                datetime.datetime.combine(self.start, datetime.time(0,0)),
                datetime.datetime.combine(self.end, datetime.time(23,59)))
            for c in occs:
                occurrences.append(c)
        occurrences.sort(key=lambda occ: occ.start)
        return occurrences

    def get_occurrence(self, occurrence):
        for (i, c) in enumerate(self.get_occurrences()):
            if c == occurrence:
                return (i, c)

    def _is_full(self, occurrence):
        p_amnt = Participation.objects.get_participations(occurrence).filter(state__in=[0,5]).count()
        return p_amnt >= self.max_participants

    def get_possible_states(self, rider, occurrence):
        """
        >>> course = Course.objects.get(pk=1)
        >>> user = User.objects.filter(username='user')[0]
        >>> user = user.get_profile()
        >>> occ = course.get_occurrences()[0] #Past occurrence
        >>> Participation.objects.all().delete()
        >>> course.get_possible_states(user, occ)
        []
        >>> occ = course.get_occurrences()[1]
        >>> course.get_possible_states(user, occ)
        [0]
        >>> cuser = User.objects.get_or_create(username='cuser', first_name='Second', last_name='Guy')[0].get_profile()
        >>> duser = User.objects.get_or_create(username='duser', first_name='Third', last_name='Guy')[0].get_profile()
        >>> occ = course.get_occurrences()[3]
        >>> p1 = course.attend(cuser, occ)
        >>> p1.state 
        0
        >>> course.get_possible_states(user, occ)
        [0]
        >>> course.max_participants = 1 
        >>> course.get_possible_states(user, occ)
        [5]
        >>> p = course.attend(user, occ)
        >>> p.state # There was no room for user -> Reserved
        5
        >>> course.get_possible_states(user, occ) # Reserved, can cancel
        [3]
        >>> p1.state = 3 # Cancel cuser to make space for user
        >>> p1.save()
        >>> course.get_possible_states(user, occ) # Reserved, and there is space
        [0,3]
        >>> p = course.attend(user, occ)
        >>> p.state
        0
        >>> course.get_possible_states(user, occ) # Can cancel when attending
        [3]
        >>> p.cancel()
        >>> p.state
        3
        >>> p1 = course.attend(cuser, occ)
        >>> p2 = course.attend(duser, occ)
        >>> p1.state = 5
        >>> p1.last_state_change_on = datetime.datetime.now()-datetime.timedelta(days=2)
        >>> p1.save(True)
        >>> p2.state = 5
        >>> p2.last_state_change_on = datetime.datetime.now()-datetime.timedelta(days=1)
        >>> p2.save(True)
        >>> course.get_possible_states(user, occ) # Canceled, but others were first, so can only reserve
        [5]
        >>> p2.state = 3 # Make some space
        >>> p2.save(True)
        >>> p2.state
        3
        >>> p1.state
        5
        >>> p.state
        3
        >>> course._is_full(occ)
        True
        >>> course.get_possible_states(user, occ) # Canceled, and there is space
        [5]
        >>> p1.state = 3
        >>> p1.save(True)
        >>> course.get_possible_states(user, occ) # Canceled, and there is space
        [0]
        """
        # If this course is in the past (end date gone), can't do anything
        if occurrence.end < datetime.datetime.now():
            return []
        p = Participation.objects.get_participation(rider, occurrence)
        # If user is already attending, can cancel
        if p and p.state == 0:
            return [3]
        # If there is space, but others are first
        parts = Participation.objects.get_participations(occurrence)
        amnt = 0
        if self._is_full(occurrence):
            for pa in parts:
                # If user has reserved and is top enough, can attend or cancel
                if pa.participant == rider and pa.state == 5:
                    return [0, 3]
                # count only reservers and attenders
                if pa.state == 0 or pa.state == 5:
                    amnt = amnt + 1
                if amnt >= self.max_participants:
                    # If user has reserved and the occ is full, can cancel
                    if p and p.state == 5:
                        return [3]
                    # Otherwise, user can reserve
                    return [5]
        # Otherwise, can attend
        return [0]

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
        from financial import ParticipationTransactionActivator
        pstates = self.get_possible_states(rider, occurrence)
        if not 0 in pstates and not 5 in pstates:
            raise AlreadyAttendingError()

        parti = Participation.objects.get_participation(rider, occurrence)
        if not parti:
            parti = Participation()
            parti.participant = rider
            parti.event = occurrence.event
            parti.start = occurrence.original_start
            parti.end = occurrence.original_end

        if 0 in pstates:
            # Max attending, set to queue, reserved
            parti.state = 0
            reversion.set_comment("Attending")
        elif 5 in pstates:
            parti.state = 5
            reversion.set_comment("Reserved")
        parti.save()
        ParticipationTransactionActivator.objects.try_create(parti, self.default_participation_fee, self.ticket_type.all())
        return parti

    @models.permalink
    def get_absolute_url(self):
        return ('stables.views.view_course', (), { 'course_id': self.id })

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
            e.end_recurring_period = datetime.datetime.combine(self.cleaned_data['end'], self.cleaned_data['endtime'])
            e.save()
            course.events.add(e)
        return course

    def save_m2m(self, *args, **kwargs):
        pass

class ParticipationManager(models.Manager):
    def get_participation(self, rider, occurrence):
        parts = self.filter(participant=rider, start=occurrence.original_start, end=occurrence.original_end)
        if not parts:
            return None
        return parts[0]

    def get_participations(self, occurrence):
        return self.filter(start=occurrence.original_start, end=occurrence.original_end, ).order_by('last_state_change_on')

ATTENDING = 0
ATTENDED = 1
SKIPPED = 2
CANCELED = 3
REJECTED = 4
RESERVED = 5
PARTICIPATION_STATES = (
    (ATTENDING, _('Attending')),
    (ATTENDED, _('Attended')),
    (SKIPPED, _('Skipped')),
    (CANCELED, _('Canceled')),
    (REJECTED, _('Rejected')),
    (RESERVED, _('Reserved')),
)
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
        return Occurrence.objects.get(event = self.event, original_start = self.start)

ENROLL_STATES = (
    (0, 'Attending'),
    (1, 'Approved'),
    (2, 'Canceled'),
    (3, 'Skipped'),
    (4, 'Rejected'),
    (5, 'Reserved'),
)
class Enroll(models.Model):
    class Meta:
        app_label = 'schedule'
    course = models.ForeignKey(Course)
    rider = models.ForeignKey(UserProfile)
    state = models.IntegerField(choices=ENROLL_STATES, default=0)
    attended_on = models.DateTimeField(default=datetime.datetime.now())
