from django import template
from stables.models import Participation
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
register = template.Library()

@register.inclusion_tag('stables/participate_button.html')
def participate_button(user, course, occurrence_index, participation):
    occ = course.get_occurrences()[occurrence_index]
    states = course.get_possible_states(user, occ)
    buttons = []

    participation_id = 0
    p = Participation.objects.get_participation(user, occ)
    if p:
        participation_id = p.id

    for s in states:
        if s == 0:
            btn_text = _('Attend')
            action = reverse('stables.views.attend_course', args=[course.id])
        elif s == 3:
            btn_text = _('Cancel')
            action = reverse('stables.views.cancel_participation', args=[course.id])
        elif s == 5:
            btn_text = _('Reserve')
            action = reverse('stables.views.attend_course', args=[course.id])
        buttons.append({ 'occurrence_index': occurrence_index, 'action': action, 'button_text': btn_text, 'participation_id': participation_id })

    return { 'buttons': buttons }
