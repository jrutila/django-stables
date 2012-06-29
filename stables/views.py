from models import HorseForm, Horse, Course, Participation, PARTICIPATION_STATES
from models import Enroll
from models import UserProfile
from models import Transaction
from models import ATTENDING, RESERVED, SKIPPED
from schedule.models import Occurrence
from django.shortcuts import render_to_response, redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
import datetime
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
import models as enum
import dateutil.parser
from django import forms

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return render_to_response(*args, **kwargs)

@require_POST
def confirm(request, action):
    context = dict(request.POST)
    del context[u'csrfmiddlewaretoken']
    return render(request, 'stables/confirm.html', { 'action': action, 'title': request.GET['title'],'back': request.META['HTTP_REFERER'], 'context': context })

def add_horse(request):
    if request.method == "POST":
        form = HorseForm(request.POST)
        if form.is_valid():
            horse = form.save()
            return redirect(horse)
    else:
        form = HorseForm()
    return render_response(request, 'stables/addhorse.html', { 'form': form })

def view_horse(request, horse_id):
    horse = Horse.objects.get(pk=horse_id)
    return render_response(request, 'stables/horse.html', { 'horse': horse })

def list_horse(request):
    horses = Horse.objects.all()
    return render_response(request, 'stables/horselist.html', { 'horses': horses })

from babel.dates import format_date
from django.utils.translation import get_language
def list_course(request):
    courses = Course.objects.exclude(end__lte=datetime.date.today())
    occs = {}
    for c in courses:
      for o in c.get_occurrences(delta=datetime.timedelta(days=6), start=datetime.date.today()):
        if not occs.has_key(o.start.hour):
          occs[o.start.hour] = {}
          for i in range(0,7):
            occs[o.start.hour][i] = []
        full = _("Space")
        if c.is_full(o):
          full = _("Full")
        occs[o.start.hour][o.start.weekday()].append((c, full))
    week = {}
    today = datetime.date.today()
    while today < datetime.date.today()+datetime.timedelta(days=7):
      week[today.weekday()] = (today, format_date(today, 'EE', locale=get_language()))
      today = today+datetime.timedelta(days=1)
    return render_response(request, 'stables/courselist.html',
            { 'courses': courses, 'occurrences': occs, 'week': week })

def view_course(request, course_id):
    course = Course.objects.get(pk=course_id)
    if (request.user.has_perm('stables.change_participation')):
      occurrences = course.get_occurrences(start=datetime.date.today()-datetime.timedelta(days=7))
    else:
      occurrences = course.get_occurrences(start=datetime.date.today())

    estates = {}
    for e in Enroll.objects.filter(course=course, state__in=[ATTENDING, RESERVED]):
      estates[e.participant] = e
      
    parts = Participation.objects.filter(event__in=course.events.all())
    occs = []

    for o in occurrences:
      pp = dict(estates) 
      for p in parts.filter(start=o.original_start):
        pp[p.participant] = p
      pp = sorted(pp.values(), key=lambda x: x.last_state_change_on )
      atnd = filter(lambda x: x.state == ATTENDING, pp)
      resv = filter(lambda x: x.state == RESERVED, pp)
      occs.append({'occurrence': o, 'attending_amount': len(atnd), 'start': o.start, 'end': o.end, 'parts': atnd+resv })

    return render_response(request, 'stables/course.html',
            { 'course': course, 'occurrences': occs })

def get_user_or_404(request, username, perm):
    if username and perm:
        return User.objects.filter(username=username)[0].get_profile()
    elif username != request.user.username:
        raise Http404
    return request.user.get_profile()

def attend_course(request, course_id):
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    course = get_object_or_404(Course, pk=course_id)
    start=dateutil.parser.parse(request.POST.get('start'))
    occurrence = course.get_occurrence(start=start) #, end=request.POST.get('end')))
    course.attend(user, occurrence)
    return redirect(request.META['HTTP_REFERER'])

def enroll_course(request, course_id):
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    course = get_object_or_404(Course, pk=course_id)
    course.enroll(user)
    return redirect(request.META['HTTP_REFERER'])

def cancel(request, course_id):
    # Only user that has right to change permission
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    pid = request.POST.get('participation_id')
    start = request.POST.get('start')
    if start:
        start = dateutil.parser.parse(start)
    if pid and int(pid) > 0:
        pid = int(pid)
        participation = get_object_or_404(Participation, pk=pid)
        participation.cancel()
        #return redirect('stables.views.modify_participations', course_id=int(course_id), occurrence_start=start.isoformat())
    elif start:
        course = get_object_or_404(Course, pk=course_id)
        occurrence = course.get_occurrence(start=start) #, end=request.POST.get('end')))
        participation = course.create_participation(user, occurrence, enum.CANCELED)
        #return redirect('stables.views.modify_participations', course_id=int(course_id), occurrence_start=start.isoformat())
    else:
        enroll = Enroll.objects.filter(course=course_id, participant=user)[0]
        enroll.cancel()
        #return redirect('stables.views.modify_enrolls', course_id=int(course_id))
    return redirect(request.META['HTTP_REFERER'])

def view_account(request):
    user = request.user.get_profile()
    return render(request, 'stables/account.html', { 'user': user })

def view_rider(request, username):
    rider = User.objects.filter(username=username)[0].get_profile()
    saldo = None
    if rider.customer and (request.user.has_perm('stables.can_view_saldo') or rider.customer.userprofile.user == request.user):
        saldo = rider.customer.saldo()
    return render_response(request, 'stables/rider.html', { 'rider': rider, 'saldo': saldo })

def view_customer(request, username):
    user = User.objects.filter(username=username)[0]
    customer = user.get_profile().customer
    if not customer:
        raise Http404
    if user != request.user and not request.user.has_perm('stables.view_transaction'):
        raise Http404
    trans = Transaction.objects.filter(active=True, customer=customer).order_by('-created_on')
    saldo = customer.saldo()
    return render_response(request, 'stables/customer.html', { 'customer': customer, 'transactions': trans, 'saldo': saldo })

class ModifyParticipationForm(forms.Form):
  PARTICIPATE_KEY_PREFIX='participate_'
  usermap={}
  def __init__(self, *args, **kwargs):
    course = kwargs.pop('course')
    occurrence = kwargs.pop('occurrence')
    participants = kwargs.pop('participants')

    super(ModifyParticipationForm, self).__init__(*args, **kwargs)

    for participant in participants:
      key = str(self.PARTICIPATE_KEY_PREFIX+'%s') % participant.user.username
      self.usermap[participant.user.username] = participant
      items = []
      states = course.get_possible_states(participant, occurrence)
      for s in PARTICIPATION_STATES:
        if s[0] != -1:
          items.append({'value': s[0], 'text': ('(*) %s' % unicode(s[1])) if s[0] in states else s[1] , 'allowed': s[0] in states })

      # Put allowed items on top
      items.sort(key=lambda x: x['allowed'], reverse=True)

      curstate = SKIPPED
      
      p = course.get_participation(participant, occurrence)
      if p:
        curstate = p.state
      else:
        # And if there is no participation, use enroll state
        e = Enroll.objects.filter(participant=participant, course=course, last_state_change_on__lt=occurrence.start)
        if e.exists():
          curstate = e[0].state

      # Sort by current state
      items.sort(key=lambda x: x['value'] == curstate, reverse=True)

      self.fields[key] = forms.ChoiceField(label=participant, choices=[(i['value'], i['text']) for i in items])

  def participations(self):
    for name, value in self.cleaned_data.items():
      if name.startswith(self.PARTICIPATE_KEY_PREFIX):
        yield (self.usermap[name[len(self.PARTICIPATE_KEY_PREFIX):]], int(value))


import dateutil.parser
@permission_required('stables.change_participation')
def modify_participations(request, course_id, occurrence_start):
    course = get_object_or_404(Course, pk=course_id)
    occurrence = None
    participations = None
    users = UserProfile.objects.filter(rider__isnull=False)
    form = None
    if occurrence_start:
        occurrence = course.get_occurrence(start=dateutil.parser.parse(occurrence_start))
        # Get both participation and enroll participants
        p_attnd = set(y.participant for y in Participation.objects.get_participations(occurrence))
        c_attnd = set(y.participant for y in Enroll.objects.get_enrolls(course, occurrence))
        attnd = p_attnd | c_attnd
        if request.method == 'POST':
          form = ModifyParticipationForm(request.POST, course=course, occurrence=occurrence, participants=attnd)
          if form.is_valid():
            for part in form.participations():
              course.create_participation(part[0], occurrence, part[1], True)
        else:
          form = ModifyParticipationForm(course=course, occurrence=occurrence, participants=attnd)
        return render(request, 'stables/participations.html', { 'course': course, 'occurrence': occurrence, 'participations': attnd, 'users': set(users) - set([k for k in attnd]), 'form': form })

class HorseParticipationForm(forms.Form):
  def __init__(self, *args, **kwargs):
    participations = kwargs['participations']
    horses = kwargs['horses']
    del kwargs['participations']
    del kwargs['horses']
    super(HorseParticipationForm, self).__init__(*args, **kwargs)
    for p in participations:
      self.fields['rider_id_'+str(p.participant.id)] = forms.ModelChoiceField(queryset=horses, label=str(p.participant), initial=p.horse, required=False)

from django.contrib.admin import widgets
class ParticipationTimeForm(forms.Form):
    new_start = forms.DateTimeField(initial=datetime.datetime.now())
    new_end = forms.DateTimeField(initial=datetime.datetime.now())

@permission_required('stables.change_participation_time')
def modify_participation_time(request, course_id, occurrence_start):
    if not occurrence_start:
        raise Http404
    course = get_object_or_404(Course, pk=course_id)
    occurrence = course.get_occurrence(start=dateutil.parser.parse(occurrence_start))
    if request.method == 'POST':
      form = ParticipationTimeForm(request.POST)
      if form.is_valid():
        occurrence.move(form.cleaned_data['new_start'], form.cleaned_data['new_end'])
        return redirect(course)
    else:
      form = ParticipationTimeForm()
      form.initial['new_start'] = occurrence.start
      form.initial['new_end'] = occurrence.end
    return render(request, 'stables/participation_time.html', { 'course': course, 'occurrence': occurrence, 'form': form })

@permission_required('stables.change_participation_horse')
def modify_participation_horses(request, course_id, occurrence_start):
    if not occurrence_start:
        raise Http404
    course = get_object_or_404(Course, pk=course_id)
    occurrence = None
    horses = Horse.objects
    occurrence = course.get_occurrence(start=dateutil.parser.parse(occurrence_start))
    parts = {}
    for a in course.full_rider(occurrence):
      p = course.get_participation(a, occurrence)
      parts[a.id] = p

    if request.method == 'POST':
      form = HorseParticipationForm(request.POST, participations=parts.values(), horses=horses)
      if form.is_valid():
        for (k,v) in form.cleaned_data.items():
          p = parts[int(k.rsplit('_')[2])]
          p.horse = v
          p.save()
        return redirect(course)
    else:
      form = HorseParticipationForm(participations=parts.values(), horses=horses)

    return render(request, 'stables/participation_horse.html', { 'course': course, 'occurrence': occurrence, 'form': form })

@permission_required('stables.change_participation')
def modify_enrolls(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrolls = Enroll.objects.filter(course=course)
    en_users = [e.participant for e in enrolls]
    users = UserProfile.objects.filter(rider__isnull=False)
    view_enrolls = []
    for e in enrolls:
      view_enrolls.append({'participant': e.participant, 'state': PARTICIPATION_STATES[e.state][1]})
    return render(request, 'stables/enrolls.html', { 'course': course, 'enrolls': view_enrolls, 'users': set(users) - set(en_users) })

from models import TicketForm
@permission_required('stables.add_ticket')
def add_tickets(request, username):
  tf = TicketForm(initial={'rider': UserProfile.objects.get(user__username=username).rider})
  if request.method == "POST":
    tf = TicketForm(request.POST)
    if tf.is_valid():
      tf.save_all()
      return redirect('stables.views.view_rider', username)
  return render(request, 'stables/addtickets.html', { 'form': tf, 'username': username })


from models import admin, RiderInfo
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

@staff_member_required
def update_rider_levels(request):
  if request.method == 'POST':
    ids = request.POST.getlist('id')
    form = admin.RiderLevelForm(request.POST)
    if form.is_valid():
      for r in UserProfile.objects.filter(id__in=ids):
        if not r.rider:
          rider = RiderInfo.objects.create(customer=r.customer)
	  rider.levels = form.cleaned_data['levels']
	  r.rider = rider
	  r.save()
	else:
	  r.rider.levels = form.cleaned_data['levels']
        r.rider.save()
      return HttpResponseRedirect('/admin/stables/riderinfo')
  else:
    ids = request.GET.get('ids').split(',')
    form = admin.RiderLevelForm()
  return render(request, 'stables/riderlevels.html', { 'form': form, 'act': reverse('stables.views.update_rider_levels'), 'riders': ids })
