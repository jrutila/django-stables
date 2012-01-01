from django import template
from stables.models import Participation, Enroll
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from urllib import urlencode
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from stables.models import Transaction
import stables.models as enum
register = template.Library()

@register.inclusion_tag('stables/participate_button.html')
def participate_button(user, course, occurrence):
    index, occ = course.get_occurrence(occurrence)
    states = course.get_possible_states(user, occ)
    buttons = []

    participation_id = 0
    start = None
    end = None
    p = Participation.objects.get_participation(user, occ)
    if p:
        participation_id = p.id
        start = p.start
        end = p.end

    for s in states:
        if s == 0:
            btn_text = _('Attend')
            action = reverse('stables.views.attend_course', args=[course.id])
        elif s == 3:
            btn_text = _('Cancel')
            action = reverse('stables.views.cancel_participation', args=[course.id])
            if p:
                part_type = ContentType.objects.get_for_model(p)
                if Transaction.objects.filter(content_type=part_type, object_id=p.id).exists():
                    action = reverse('stables.views.confirm', kwargs={'action':action})+"?"+urlencode({'title': ugettext('You still have to pay. Are you sure you want to cancel?')})
        elif s == 5:
            btn_text = _('Reserve')
            action = reverse('stables.views.attend_course', args=[course.id])
        buttons.append({ 'occurrence_index': index, 'action': action, 'button_text': btn_text, 'participation_id': participation_id, 'username': user.user.username})

    return { 'buttons': buttons }

@register.inclusion_tag('stables/_participants.html', takes_context=True)
def participants(context, course, occurrence):
    user = context['request'].user
    otherparts = []
    mypart = None
    ownpart = False
    if user.is_authenticated():
        rider = user.get_profile()
        if user.has_perm('stables.course_view_participants'):
            # Admin can view all
            parts = Participation.objects.get_participations(occurrence)
            if not parts.filter(participant=rider):
                ownpart = True
            for e in Enroll.objects.filter(course=course, state=enum.ATTENDING).order_by('last_state_change_on'):
                epart = Participation()
                epart.participant = e.participant
                epart.start = occurrence.original_start
                epart.end = occurrence.original_end
                epart.event = occurrence.event
                if not parts.filter(participant=epart.participant):
                    otherparts.append(epart)
                if epart.participant == rider:
                    ownpart = False
        else:
            parts = [Participation.objects.get_participation(rider, occurrence)]
            if parts[0] == None:
                parts = [Enroll.objects.filter(course=course, participant=rider)]
                if not parts[0]:
                    parts = []
                else:
                    epart = Participation()
                    epart.participant = parts[0][0].participant
                    epart.start = occurrence.original_start
                    epart.end = occurrence.original_end
                    epart.event = occurrence.event
                    parts[0] = epart
    else:
        return
    return { 'participations': otherparts+list(parts), 'course': course, 'occurrence': occurrence, 'rider': rider, 'mypart': mypart }
