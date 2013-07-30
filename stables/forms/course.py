from django import forms
from stables.models import Course
from stables.models import Participation
from schedule.models import Event
from schedule.models import Calendar
from schedule.models import Rule
import datetime
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout, Fieldset, ButtonHolder

class CourseFormHelper(FormHelper):
    form_class = 'blueForms'
    form_method = 'post'

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = ('created_on', 'creator', 'course_fee', 'events')

    starttime = forms.TimeField(required=False)
    endtime = forms.TimeField(required=False)
    take_into_account = forms.DateTimeField(required=False, initial=datetime.datetime.now())

    def __init__(self, *args, **kwargs):
      super(CourseForm, self).__init__(*args, **kwargs)
      self.helper = CourseFormHelper()
      self.helper.layout = Layout(
            Fieldset(
              _('Basic information'), 
              'name','start', 'end', 'max_participants', 'allowed_levels' 
              ),
            Fieldset(
              _('Recurring information'),
              HTML('<strong>%s</strong>' % _('Do NOT input anything here if you have one time events.')),
              'starttime',
              'endtime',
              ),
            Fieldset(
              _('Payment information'),
              'default_participation_fee', 'ticket_type',
              ),
            Fieldset(
              _('Advanced settings'),
              'take_into_account',
              ),
            ButtonHolder(
              Submit('submit', 'Submit')
              )
          )

      if self.instance.pk:
        last_event = CourseForm.get_course_last_event(self.instance)
        if last_event and last_event.rule:
          self.initial['starttime'] = last_event.start.time()
          self.initial['endtime'] = last_event.end.time()
          if last_event.end_recurring_period:
              self.initial['end'] = last_event.end_recurring_period.date()

    def save(self, force_insert=False, force_update=False, commit=True):
        instance = super(forms.ModelForm, self).save(commit=True)
        last_event = CourseForm.get_course_last_event(instance)
        if self.cleaned_data['starttime'] and self.cleaned_data['endtime'] and (not last_event or (self.cleaned_data['starttime'] != last_event.start.time() or self.cleaned_data['endtime'] != last_event.end.time())):
            next_start = self.cleaned_data['start']
            next_end = self.cleaned_data['start']
            if last_event:
              next_start = last_event.next_occurrence().start.date()
              next_end = last_event.next_occurrence().end.date()
            # Create a new event with starttime and endtime
            e = Event()
            e.start = datetime.datetime.combine(next_start, self.cleaned_data['starttime'])
            e.end = datetime.datetime.combine(next_end, self.cleaned_data['endtime'])
            e.save()
            # End the last event
            if last_event:
              last_event.end_recurring_period=last_event.next_occurrence().end-datetime.timedelta(days=7)
              last_event.save()
            # Update event title
            e.title = self.cleaned_data['name']
            e.calendar = Calendar.objects.get(pk=1)
            e.creator = self.user
            e.created_on = datetime.datetime.now()
            e.rule = Rule.objects.get(pk=1)
            if self.cleaned_data['end']:
              e.end_recurring_period = datetime.datetime.combine(self.cleaned_data['end'], self.cleaned_data['endtime'])
            e.save()
            instance.events.add(e)
            instance.save()
            for p in Participation.objects.filter(event=last_event, start__gte=next_start):
              p.event=e
              p.start=datetime.datetime.combine(p.start.date(), e.start.time())
              p.end=datetime.datetime.combine(p.end.date(), e.end.time())
              p.save()
        elif last_event:
            if not self.cleaned_data['end'] and last_event.end_recurring_period:
                last_event.end_recurring_period = None
                last_event.save()
            elif self.cleaned_data['end'] and (not last_event.end_recurring_period or last_event.end_recurring_period.date() != self.cleaned_data['end']):
                last_event.end_recurring_period = datetime.datetime.combine(self.cleaned_data['end'], self.cleaned_data['endtime'])
                last_event.save()

        # Update all names
        if self.cleaned_data['name']:
          for e in instance.events.all():
            e.title = self.cleaned_data['name']
            e.save()

        return instance

    def save_m2m(self, *args, **kwargs):
        pass

    @classmethod
    def get_course_last_event(csl, course):
        if course.events.filter(rule__isnull=False).count() > 0:
          return course.events.filter(rule__isnull=False).order_by('-start')[0]
        return None

class AddEventForm(forms.Form):
    date = forms.DateField()
    start = forms.TimeField()
    end = forms.TimeField()

    def __init__(self, *args, **kwargs):
        self.helper = CourseFormHelper()
        self.helper.layout = Layout(
          Fieldset(
            _('Event information'), 
            'date','start', 'end'
          ),
          ButtonHolder(
            Submit('submit', 'Submit')
          )
        )
        self.user = kwargs.pop('user')
        self.course = kwargs.pop('course')
        super(AddEventForm, self).__init__(*args, **kwargs)

    def save_event(self):
        event = Event()
        event.start = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['start'])
        event.end = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['end'])
        event.title = self.course.name
        event.creator = self.user
        event.calendar = Calendar.objects.get(pk=1)
        event.save()
        self.course.events.add(event)
        self.course.save()

class ChangeEventForm(AddEventForm):
    cancel = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.event=kwargs.pop('event')
        super(ChangeEventForm, self).__init__(*args, **kwargs)
        btn = self.helper.layout.fields.pop()
        self.helper.layout.fields.append(Fieldset(
            _('Cancel event'),
            'cancel'
            )
        )
        self.helper.layout.fields.append(btn)
        self.initial['date'] = self.event.start.date()
        self.initial['start'] = self.event.start.time()
        self.initial['end'] = self.event.end.time()
        self.initial['cancel'] = self.event.cancelled

    def save_event(self):
        if self.cleaned_data['cancel'] and not self.event.cancelled:
            self.event.cancel()
        elif not self.cleaned_data['cancel'] and self.event.cancelled:
            self.event.uncancel()
        start = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['start'])
        end = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['end'])
        self.event.move(start, end)
