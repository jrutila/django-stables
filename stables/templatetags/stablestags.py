from django import template
from stables.models import Participation, Enroll
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from urllib import urlencode
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from stables.models import Transaction
from schedule.models import Event
import datetime

from django.core.exceptions import ObjectDoesNotExist
from stables.models import PARTICIPATION_STATES
from stables.models import ATTENDING, CANCELED, RESERVED, SKIPPED

import stables.models as enum
register = template.Library()

@register.inclusion_tag('stables/render_field.html')
def render_field(form, course, participation, name, occurrence=None, attributes=''):
    field = form.get_field(course, participation, name, occurrence)
    return {'errors': field.errors, 'widget': make_widget(field, attributes)}

def make_widget(field,attributes):
    attr = {}
    if attributes:
        attrs = attributes.split(",")
        if attrs:
            for at in attrs:
                key,value = at.split("=")
                attr[key] = value
    return field.as_widget(attrs=attr)

# TODO: This is not related to stables per se, move it!
@register.inclusion_tag('stables/date_picker.html', takes_context=True)
def date_picker(context):
    picker = {}
    current_view = context['request'].current_view
    if 'date' in current_view['kwargs']:
      today = datetime.datetime.strptime(current_view['kwargs']['date'], '%Y-%m-%d').date()
    else:
      today = datetime.date.today()
    picker['yesterday_url'] = reverse(current_view['name'], kwargs={'date': today-datetime.timedelta(days=1) })
    picker['tomorrow_url'] = reverse(current_view['name'], kwargs={'date': today+datetime.timedelta(days=1) })
    picker['base_url'] = reverse(current_view['name'])
    picker['today'] = today
    return picker

@register.inclusion_tag('stables/pay_button.html', takes_context=True)
def pay_button(context, participation, ticket_type=None):
    button = { 'button_text': _('Cash') }
    button['redirect'] = reverse('stables.views.widget')
    button['participation_id'] = participation.id
    button['action'] = reverse('stables.views.pay')
    if ticket_type:
      button['ticket'] = ticket_type.id
      button['button_text'] = ticket_type.name
    return { 'button': button }

@register.inclusion_tag('stables/participate_button.html', takes_context=True)
def participate_button(context, user, course, occurrence=None):
    buttons = []
    has_change_perm=context['request'].user.has_perm('stables.change_participation')

    if isinstance(course, Event):
      course = course.course_set.all()[0]

    # If occurrence is none, this is participate button for course enroll
    if occurrence:
      occ = occurrence
      states = course.get_possible_states(user, occ, has_change_perm)


      participation_id = 0
      start = None
      end = None
      p = Participation.objects.get_participation(user, occ)

      if p:
          participation_id = p.id
          start = p.start
          end = p.end
          if p.state != SKIPPED and has_change_perm:
            states.append(SKIPPED)

      for s in states:
          if s == ATTENDING:
              btn_text = _('Attend')
              action = reverse('stables.views.attend_course', args=[course.id])
          elif s == SKIPPED:
              btn_text = _('Skipped')
              action = reverse('stables.views.skip', args=[course.id])
          elif s == CANCELED:
              btn_text = _('Cancel')
              action = reverse('stables.views.cancel', args=[course.id])
              if p and not has_change_perm:
                  if Transaction.objects.filter(
                      content_type=ContentType.objects.get_for_model(p),
                      object_id=p.id).exists():
                      action = reverse('stables.views.confirm', kwargs={'action':action})+"?"+urlencode({'title': ugettext('You still have to pay. Are you sure you want to cancel?').encode('utf-8')})
          elif s == RESERVED:
              btn_text = _('Reserve')
              action = reverse('stables.views.attend_course', args=[course.id])
          buttons.append({ 'start': occ.start, 'end': occ.end, 'action': action, 'button_text': btn_text, 'participation_id': participation_id, 'username': user.user.username})
    else:
      states = course.get_possible_states(user)
      for s in states:
        if s == ATTENDING:
          btn_text = _('Enroll')
          action = reverse('stables.views.enroll_course', args=[course.id])
        elif s == CANCELED:
          btn_text = _('Cancel')
          action = reverse('stables.views.cancel', args=[course.id])
        elif s == RESERVED:
          btn_text = _('Reserve')
          action = reverse('stables.views.enroll_course', args=[course.id])
        buttons.append({'action': action, 'button_text': btn_text, 'username': user.user.username })

    return { 'buttons': buttons }

@register.filter()
def state(state):
  return PARTICIPATION_STATES[state][1]

from isoweek import Week
@register.filter()
def week_range(monday, before=3, after=4):
  r = []
  year = Week.withdate(monday).year
  week = Week.withdate(monday).week
  for i in range(week-before, week+after):
    y = year
    if i <=0:
      i = 52+i
      y = y-1
    if i > 52:
      i = i-52
      y = y+1
    if y == datetime.date.today().year:
      y = None
    r.append((i, y))
  return r

@register.filter
def getitem ( item, string ):
  return item.get(string,'')
