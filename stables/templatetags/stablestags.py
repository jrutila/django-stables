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

from django.core.urlresolvers import NoReverseMatch
from stables.models import PARTICIPATION_STATES
from stables.models import ATTENDING, CANCELED, RESERVED, SKIPPED

import stables.models as enum
from stables.utils import getPaymentLink
from django.utils import timezone

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
    button['redirect'] = context['request'].META.get('HTTP_REFERER', reverse('newboard'))
    button['participation_id'] = participation.id
    button['action'] = reverse('stables.views.pay')
    if ticket_type:
      button['ticket'] = ticket_type.id
      button['button_text'] = ticket_type.name
    return { 'button': button }

@register.inclusion_tag('stables/participate_button.html', takes_context=True)
def participate_button(context, participation, redirect=None):
    buttons = []
    #has_change_perm=context['request'].user.has_perm('stables.change_participation')

    if not participation:
        return { 'buttons': buttons }

    if redirect:
      try:
        redirect = reverse(redirect)
      except NoReverseMatch:
        redirect = redirect
    else:
      redirect = context['request'].META.get('HTTP_REFERER', reverse('newboard'))

    states = participation.get_possible_states()

    for s in states:
        if s == ATTENDING:
          btn_text = _('Attend')
          action = reverse('participation_attend', args=[participation.id])
        elif s == CANCELED:
            btn_text = _('Cancel')
            if participation.id:
                action = reverse('participation_cancel', args=[participation.id])
            else:
                action = reverse('participation_cancel', kwargs={
                    'event': participation.event.id,
                    'start': timezone.make_naive(participation.start, timezone.get_current_timezone()).isoformat()
                })
        elif s == RESERVED:
          btn_text = _('Reserve')
          action = reverse('participation_attend', args=[participation.id])
        btn = {
            'start': participation.start,
            'end': participation.end,
            'action': action,
            'button_text': btn_text,
            'participation_id': participation.id,
            'username': participation.participant.user.username}
        if redirect:
          btn['redirect'] = redirect
        buttons.append(btn)

    return { 'buttons': buttons }

@register.filter()
def state(state):
  return PARTICIPATION_STATES[state][1]

@register.simple_tag()
def short_pay(participation):
    return reverse('shop-pay', kwargs={ 'hash': getPaymentLink(participation.id).hash })

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

from django.http import QueryDict
@register.filter
def qstring_get(qstring, key):
    qdict = QueryDict(qstring)
    if key not in qdict:
        return None
    return qdict[key]


from django.template import Node
class GKNode(Node):
    def __init__(self, content, test):
        self.content = content
        self.test = test

    def render(self, context):
        if self.test:
            return self.content.render(context)
        return ""

@register.tag
def gatekeeper(parser, token):
    import django_settings
    tag, feature = token.contents.split()
    content = parser.parse(['gatekeeper', 'endgatekeeper'])
    parser.next_token()
    test = False

    if feature == 'merchant':
        test = django_settings.exists('merchant_id')

    return GKNode(content, test)
