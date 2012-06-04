from django import template
from stables.models import Participation, Enroll
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from urllib import urlencode
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from stables.models import Transaction
import datetime

from django.core.exceptions import ObjectDoesNotExist
from stables.models import PARTICIPATION_STATES
from stables.models import ATTENDING, CANCELED, RESERVED, SKIPPED

import stables.models as enum
register = template.Library()

@register.inclusion_tag('stables/participate_button.html')
def participate_button(user, course, occurrence=None):
    buttons = []

    # If occurrence is none, this is participate button for course enroll
    if occurrence:
      occ = occurrence
      states = course.get_possible_states(user, occ)

      participation_id = 0
      start = None
      end = None
      p = Participation.objects.get_participation(user, occ)

      if p:
          participation_id = p.id
          start = p.start
          end = p.end

      for s in states:
          if s == ATTENDING:
              btn_text = _('Attend')
              action = reverse('stables.views.attend_course', args=[course.id])
          elif s == CANCELED:
              btn_text = _('Cancel')
              action = reverse('stables.views.cancel', args=[course.id])
              if p:
                  part_type = ContentType.objects.get_for_model(p)
                  if Transaction.objects.filter(content_type=part_type, object_id=p.id).exists():
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
