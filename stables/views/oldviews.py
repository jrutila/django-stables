from stables.models import Horse, Course, Participation, PARTICIPATION_STATES, InstructorParticipation
from stables.models import InstructorInfo
from stables.models import Enroll
from stables.models import UserProfile
from stables.models import pay_participation
from stables.models import Transaction, Ticket, TicketType
from stables.models import ATTENDING, RESERVED, SKIPPED, CANCELED
from stables.models import Accident
from stables.models import financial
from schedule.models import Occurrence, Event, Calendar
from django.shortcuts import render_to_response, redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.models import Q, Count
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
import operator
import datetime
import time
from isoweek import Week
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
import stables.models as enum
import dateutil.parser
from django import forms
import reversion
from collections import defaultdict

from django.utils.safestring import mark_safe
from stables.models.common import _count_saldo


def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return render_to_response(*args, **kwargs)

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
    horse = get_object_or_404(Horse, pk=horse_id, public=True)
    return render_response(request, 'stables/horse.html', { 'horse': horse })

def list_horse(request):
    horses = Horse.objects.filter((Q(last_usage_date__gte=datetime.date.today()) | Q(last_usage_date__isnull=True)), public=True)
    return render_response(request, 'stables/horselist.html', { 'horses': horses })

class HorseModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.nickname

class ReportForm(forms.Form):
    horses = HorseModelMultipleChoiceField(queryset=Horse.objects.all(), widget=forms.CheckboxSelectMultiple())
    report_date_start = forms.DateField()
    report_date_end = forms.DateField(required=False)

def report(request):
    form = ReportForm(request.GET)
    if form.is_valid():
      report_date_start = form.cleaned_data['report_date_start']
      report_date_end = form.cleaned_data['report_date_end']
      if not report_date_end:
        report_date_end = report_date_start
      horses = form.cleaned_data['horses']
      for h in horses:
        parts = Participation.objects.filter(state=ATTENDING, horse=h, start__gte=report_date_start, end__lt=report_date_end+datetime.timedelta(days=1))
        h.participations = {"total": 0}
        for p in parts:
          if not p.start.date() in h.participations:
            h.participations[p.start.date()] = 0
          h.participations[p.start.date()] = h.participations[p.start.date()]+1
          h.participations["total"] = h.participations["total"] + 1
      report_interval = []
      ri = report_date_start
      while ri <= report_date_end:
        report_interval.append(ri)
        ri = ri + datetime.timedelta(days=1)
      return render_response(request, 'stables/horsereport/report.html', { 'horses': horses, 'report_interval': report_interval })
    else:
      return render_response(request, 'stables/horsereport/index.html', { 'form': form })

def _get_week(today):
    week = {}
    for i in range(0,6):
      week[today.weekday()] = (today, format_date(today, 'EE dd.MM', locale=get_language()))
      today = today+datetime.timedelta(days=1)
    return week

from babel.dates import format_date
from django.utils.translation import get_language
from django.db.models import Max
def list_course(request, week=None):
    if (request.user.has_perm('stables.change_participation')):
      if request.is_mobile:
        return redirect('stables.views.widget')
      return redirect('newboard')
    if week == None:
        week = datetime.date.today().isocalendar()[1]
    week = int(week)
    year = int(request.GET.get('year', datetime.date.today().year))

    monday = datetime.datetime(*(Week(year, week).monday().timetuple()[:6]))
    sunday = monday+datetime.timedelta(days=6, hours=23, minutes=59)
    courses = Course.objects.exclude(end__lt=sunday).annotate(start_hour=Max('events__start')).order_by('start_hour')
    occs = {}
    for c in courses:
      for o in c.get_occurrences(delta=datetime.timedelta(days=6), start=monday):
        if not occs.has_key(o.start.hour):
          occs[o.start.hour] = {}
          for i in range(0,7):
            occs[o.start.hour][i] = []
        full = _("Space")
        if c.is_full(o):
          full = _("Full")
        ins = InstructorParticipation.objects.filter(event=o.event, start=o.start, end=o.end)
        occs[o.start.hour][o.start.weekday()].append((c, full, ins[0] if ins else None, o, request.user.userprofile if request.user.is_authenticated() else None))
    week = _get_week(monday)
    today_week = Week.thisweek().week
    return render_response(request, 'stables/courselist.html',
            { 'courses': courses, 'occurrences': occs, 'week_dates': week, 'week': Week.withdate(monday).week, 'week_range': [(today_week,), (today_week+1,), (today_week+2,)] })




@permission_required('stables.view_participations')
def daily(request, date=None):
    if date == None:
      date = datetime.date.today()
    else:
      date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    participations = Participation.objects.filter(state=ATTENDING, start__gte=date, end__lt=date+datetime.timedelta(days=1))
    # directory is not sorted
    dir_events = {}
    # this is the sorted list of event tuples
    events = []
    for p in sorted(participations, key=lambda part: part.event.start.hour):
      if not p.event in dir_events:
        dir_events[p.event] = []
        events.append((p.event, dir_events[p.event]))
      dir_events[p.event].append(p)

    return render_response(request, 'stables/daily.html', { 'daily_date': date, 'events': events })

@permission_required('stables.add_transaction')
def pay(request):
    pid = request.POST.get('participation_id')
    tid = request.POST.get('ticket')
    participation = Participation.objects.get(id=pid)
    if tid:
        pay_participation(participation, ticket=TicketType.objects.get(id=tid))
    else:
        pay_participation(participation)
    return request_redirect(request)

@permission_required('stables.view_transaction')
def widget(request, date=None):
    if date == None:
      date = datetime.date.today()
    else:
      date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    participations = Participation.objects.filter(start__gte=date, end__lt=date+datetime.timedelta(days=1)).order_by('id')
    # directory is not sorted
    dir_events = {}
    # this is the sorted list of event tuples
    events = []

    transactions = list(Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id__in=participations).order_by('object_id', 'created_on').prefetch_related('ticket_set'))
    participations = list(participations)

    p_id = 0
    t_id = 0
    transbypart = defaultdict(list)
    while t_id < len(transactions) and p_id < len(participations):
        part = participations[p_id]
        #if part.participant.user.first_name == "Tuija":
        if not hasattr(part, 'saldo'):
            setattr(part, 'transactions', [])
            setattr(part, 'saldo', 0)
            setattr(part, 'ticket_used', None)
        participations[p_id] = part
        t = transactions[t_id]
        if part.id == t.object_id:
            transbypart[part].append(t)
            # TODO: Count this only when we have the last saldo
            part.saldo = _count_saldo(transbypart[part])[0]
            part.transactions.append(t)
            t_id = t_id + 1
        else:
            p_id = p_id + 1

    for p in sorted(participations, key=lambda part: (part.event.start.hour, part.state)):
      if not p.event in dir_events:
        dir_events[p.event] = []
        events.append((p.event, dir_events[p.event]))
      dir_events[p.event].append(p)
    return render_response(request, 'stables/widget.html', { 'events': events })

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

    instructors = InstructorParticipation.objects.filter(event__in=course.events.all())

    for o in occurrences:
      pp = dict(estates) 
      for p in parts.filter(start=o.start):
        pp[p.participant] = p
      pp = sorted(pp.values(), key=lambda x: x.last_state_change_on )
      atnd = filter(lambda x: x.state == ATTENDING, pp)
      resv = filter(lambda x: x.state == RESERVED, pp)
      instructors = InstructorParticipation.objects.filter(event__in=course.events.all(), start=o.start)
      occs.append({'occurrence': o, 'attending_amount': len(atnd), 'start': o.start, 'end': o.end, 'parts': atnd+resv, 'instructors': instructors })


    return render_response(request, 'stables/course.html',
            { 'course': course, 'occurrences': occs })

def get_user_or_404(request, username, perm):
    if username and perm:
        return User.objects.filter(username=username)[0].userprofile
    elif username != request.user.username:
        raise Http404
    return request.user.get_profile()

def request_redirect(request):
    redir = request.POST.get('redirect', request.META['HTTP_REFERER'])
    if request.POST.get('redirect') == u'':
      redir = request.META['HTTP_REFERER']
    return redirect(redir)

def attend_course(request, course_id):
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    course = get_object_or_404(Course, pk=course_id)
    start=dateutil.parser.parse(request.POST.get('start'))
    occurrence = course.get_occurrence(start=start) #, end=request.POST.get('end')))
    if request.user.has_perm('stables.change_participation'):
      course.create_participation(user, occurrence, ATTENDING, True)
    else:
      course.attend(user, occurrence)
    return request_redirect(request)

def enroll_course(request, course_id):
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    course = get_object_or_404(Course, pk=course_id)
    course.enroll(user)
    return request_redirect(request)


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
    elif start:
        course = get_object_or_404(Course, pk=course_id)
        occurrence = course.get_occurrence(start=start) #, end=request.POST.get('end')))
        participation = course.create_participation(user, occurrence, enum.CANCELED)
    else:
        enroll = Enroll.objects.filter(course=course_id, participant=user)[0]
        enroll.cancel()
    return request_redirect(request)

def skip(request, course_id):
    # Only user that has right to change permission
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    pid = request.POST.get('participation_id')
    start = request.POST.get('start')
    if start:
        start = dateutil.parser.parse(start)
    if pid and int(pid) > 0:
        pid = int(pid)
        participation = get_object_or_404(Participation, pk=pid)
        participation.state = SKIPPED
        participation.save()
    return request_redirect(request)

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
          items.append({'value': s[0], 'text': ('(*) %s' % str(s[1])) if s[0] in states else s[1] , 'allowed': s[0] in states })

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
      self.fields['rider_id_'+str(p.participant.id)] = MyModelChoiceField(queryset=horses, label=str(p.participant), initial=p.horse, required=False)

from django.contrib.admin import widgets

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

from stables.models import admin, RiderInfo, CustomerInfo
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

