from django import forms
from stables.models import Course
from stables.models import Participation
from schedule.models import Event
from schedule.models import Calendar
from schedule.models import Rule
import datetime
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout, Fieldset, ButtonHolder

from django.utils import timezone

class CourseFormHelper(FormHelper):
    form_class = 'blueForms'
    form_method = 'post'

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = ('created_on', 'creator', 'course_fee', 'events')

    starttime = forms.TimeField(label=_('Start time'), required=False)
    endtime = forms.TimeField(label=_('End time'), required=False)
    take_into_account = forms.DateTimeField(label=_('Take changes into acccount on'), required=False, initial=datetime.datetime.now())

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

    def save(self):
        instance = super(CourseForm, self).save(commit=False)
        instance.save(
                starttime=self.cleaned_data['starttime']
               ,endtime=self.cleaned_data['endtime']
               ,since=self.cleaned_data['take_into_account'])
        return instance

    def clean_take_into_account(self):
        data = self.cleaned_data['take_into_account']
        if not self.instance.id:
            return data
        if data < timezone.now():
            data = timezone.now()
        events = self.instance.events.filter(rule__isnull=False)
        if data < events.latest('start').start:
            after = events.order_by('-id')[1].end_recurring_period
            if data <= after:
                raise forms.ValidationError(_("This time must be after %s") % after)
        return data

    def clean(self):
        cleaned_data = super(CourseForm, self).clean()
        if cleaned_data['end'] and cleaned_data['end'] <= datetime.datetime.now().date() and (
                'starttime' in self.changed_data or
                'endtime' in self.changed_data):
            raise forms.ValidationError(_("You cannot change start time or end time on ended course"))
        return cleaned_data

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

    def save(self):
        event = Event()
        event.start = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['start'])
        event.end = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['end'])
        event.title = self.course.name
        event.creator = self.user
        event.calendar = Calendar.objects.get(pk=1)
        event.save()
        self.course.events.add(event)

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
        start = timezone.localtime(self.event.start)
        end = timezone.localtime(self.event.end)
        self.initial['date'] = start.date()
        self.initial['start'] = start.timetz()
        self.initial['end'] = end.timetz()
        self.initial['cancel'] = self.event.cancelled

    def save(self):
        if self.cleaned_data['cancel'] and not self.event.cancelled:
            self.event.cancel()
        elif not self.cleaned_data['cancel'] and self.event.cancelled:
            self.event.uncancel()
        start = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['start'])
        end = datetime.datetime.combine(self.cleaned_data['date'], self.cleaned_data['end'])
        self.event.move(start, end)
