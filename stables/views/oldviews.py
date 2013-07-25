from stables.models import HorseForm, Horse, Course, Participation, PARTICIPATION_STATES, InstructorParticipation, EventMetaData
from stables.models import InstructorInfo
from stables.models import Enroll
from stables.models import UserProfile
from stables.models import pay_participation
from stables.models import Transaction, Ticket, TicketType
from stables.models import ATTENDING, RESERVED, SKIPPED, CANCELED
from stables.models import Accident, AccidentForm
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
      return redirect('stables.views.dashboard')
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
        occs[o.start.hour][o.start.weekday()].append((c, full, ins[0] if ins else None, o, request.user.get_profile() if request.user.is_authenticated() else None))
    week = _get_week(monday)
    today_week = Week.thisweek().week
    return render_response(request, 'stables/courselist.html',
            { 'courses': courses, 'occurrences': occs, 'week_dates': week, 'week': Week.withdate(monday).week, 'week_range': [(today_week,), (today_week+1,), (today_week+2,)] })

class ParticipantLink(forms.Widget):
  def __init__(self, participation, attrs=None, required=True):
    self.attrs = attrs or {}
    self.required = required
    self.participation = participation

  def render(self, name, value, attrs=None):
    output = []
    output.append('<span class="ui-stbl-db-user">')
    if self.participation.id:
      link_text = 'ok'
      link_title = ''
      if self.participation.used_ticket:
        link_title = self.participation.used_ticket.type
      else:
        link_title = ugettext('Cash')
      if self.participation.saldo < 0:
        link_text = '<span style="color: yellow;">&#8364;</span>'
        link_title = self.participation.saldo
      if len(self.participation.transactions) == 0:
        link_text = '<span style="color: cyan;">f</span>'
        link_title = ugettext('No transactions')
      output.append('<a href="%s" title="%s">%s</a>' % (
          reverse('stables.views.widget_user', args=[self.participation.id])
          ,link_title, link_text
          )
        )
    output.append('<a href="%s">%s</a>' % (
          self.participation.participant.get_absolute_url(),
          self.participation.participant.__unicode__())
        )
    if hasattr(self.participation, 'accident'):
        output.append("X")
    output.append('</span>')
    return mark_safe(u'\n'.join(output))
        #% (reverse('stables.views.widget_user', args=[self.participation.id]),

class DashboardForm(forms.Form):
  participation_map = dict()
  course_occ_map = dict()
  participations = []
  horses = None
  timetable = {}
  changed_participations = []
  deleted_participations = []
  already_changed = set()
  newparts = {}

  def __init__(self, *args, **kwargs):
    self.courses = kwargs.pop('courses')
    self.week = kwargs.pop('week')
    self.horses = kwargs.pop('horses')
    self.year = kwargs.pop('year')
    self.timetable = {}
    self.participation_map = {}
    self.changed_participations = []
    self.already_changed = set()
    self.monday = datetime.datetime(*(Week(self.year, self.week).monday().timetuple()[:6]))
    self.sunday = self.monday+datetime.timedelta(days=6, hours=23, minutes=59)
    super(DashboardForm, self).__init__(*args, **kwargs)

    # Get all instructors
    instructors = InstructorParticipation.objects.get_participations(self.monday, self.sunday)
    ii = dict()
    for (o, (c, ins)) in instructors.items():
        if ins:
          if not c.id in ii:
              ii[c.id] = {}
          if not o.start in ii[c.id]:
              ii[c.id][o.start] = ins

    # Get all metadata
    metas = EventMetaData.objects.get_metadatas(self.monday, self.sunday)
    ee = dict()
    for (o, (c, met)) in metas.items():
        if met:
          if not c.id in ee:
              ee[c.id] = {}
          if not o.start in ee[c.id]:
              ee[c.id][o.start] = met

    participations = Participation.objects.generate_attending_participations(self.monday, self.sunday)
    accidents = Accident.objects.filter(at__gte=self.monday, at__lte=self.sunday)

    parts = [ p for (occ, (cou, par)) in participations.items() for p in par ]
    transactions = Transaction.objects.get_transactions(parts)

    for (o, (c, parts)) in participations.items():
        if not self.timetable.has_key(o.start.hour):
          self.timetable[o.start.hour] = {}
          for i in range(0,7):
            self.timetable[o.start.hour][i] = []
        ll = []
        for part in [pp for pp in sorted(parts, key=lambda p: p.state) if pp.state == ATTENDING]:
          ll.append(self.add_or_update_part(c, part))
          for acc in [acc for acc in accidents if acc.at >= part.start and acc.at <= part.end and acc.rider == part.participant.rider]:
            part.accident = acc
        neu = Participation()
        neu.participant = UserProfile()
        neu.participant.id = 0
        neu.participant.user = User()
        neu.event = o.event
        neu.start = o.start
        neu.end = o.end
        ll.append(self.add_or_update_part(c, neu))
        for part in [pp for pp in sorted(parts, key=lambda p: p.state) if pp.state != ATTENDING]:
          ll.append(self.add_or_update_part(c, part))

        for part in [ pp for pp in parts if pp.id]:
          part.transactions = [tt for tt in transactions if tt.object_id == part.id]
          part.saldo, part.used_ticket = financial._count_saldo(part.transactions)

        # Instructor participaton
        field = MyModelChoiceField(queryset=InstructorInfo.objects.all(), required=False, initial=ii[c.id][o.start][0].instructor.instructor.id if c.id in ii and o.start in ii[c.id] else None, show_hidden_initial=True)

        key = 'c%s_s%s_e%s_instructor' % (c.id, o.start.isoformat(), o.end.isoformat())
        self.fields[key] = field
        self.course_occ_map[key] = (c, o)
        cop = (c, o, ll, ii[c.id][o.start] if c.id in ii and o.start in ii[c.id] else [])
        self.timetable[o.start.hour][o.start.weekday()].append(cop)

        # Notes
        field = forms.CharField(required=False, widget=forms.Textarea, initial=ee[c.id][o.start][0].notes if c.id in ee and o.start in ee[c.id] else None, show_hidden_initial=True)
        key = 'c%s_s%s_e%s_notes' % (c.id, o.start.isoformat(), o.end.isoformat())
        self.fields[key] = field
        self.course_occ_map[key] = (c, o)
        #cop = (c, o, ll, ii[c.id][o.start] if c.id in ii and o.start in ii[c.id] else [])
        #self.timetable[o.start.hour][o.start.weekday()].append(cop)


  def add_or_update_part(self, course, part):
    if self.participation_map.has_key(self.part_hash(part)):
      for o in self.participation_map[self.part_hash(part)]:
        del self.fields[o]
        del self.participation_map[o]
      self.participation_map[self.part_hash(part)] = set()

    horse_field = MyModelChoiceField(queryset=self.horses, initial=part.horse, required=False, show_hidden_initial=True)
    horse_key = self.add_field(course, part, 'horse', horse_field)

    state_field = forms.ChoiceField(initial=part.state, choices=PARTICIPATION_STATES, required=False)
    state_key = self.add_field(course, part, 'state', state_field)

    note_field = forms.CharField(initial=part.note, widget=forms.Textarea, required=False, show_hidden_initial=True)
    note_key = self.add_field(course, part, 'note', note_field)

    if not part.participant.id: # Only new participations
      participant_field = forms.CharField(
          initial='',
          show_hidden_initial=True,
          required=False)
    else:
      participant_field = forms.CharField(
          initial='',
          required=False,
          widget=ParticipantLink(participation=part))

    participant_key = self.add_field(course, part, 'participant', participant_field)
    return (horse_key, participant_key, state_key, note_key)

  def _post_clean(self):
    for k in self.changed_data:
      key = k
      if key not in self.data:
        continue
      self.fields[key].widget.attrs['class'] = 'changed'
      self.fields[key].show_hidden_initial = False
      if 'instructor' in k:
        (c,o) = self.course_occ_map[key]
        id = self.data[k]
        if id:
          usrprf = UserProfile.objects.get(instructor__id=self.data[k])
          instrprt = InstructorParticipation()
          instrprt.instructor = usrprf
          instrprt.event = o.event
          instrprt.start = o.start
          instrprt.end = o.end
          self.changed_participations.append(instrprt)
        else:
          instrprt = InstructorParticipation.objects.filter(event=o.event, start=o.start, end=o.end)
          self.deleted_participations.append(instrprt)
        continue
      if  'notes' in k:
        (c,o) = self.course_occ_map[key]
        eventmeta, created = EventMetaData.objects.get_or_create(event=o.event, start=o.start, end=o.end)
        eventmeta.notes = self.data[k]
        self.changed_participations.append(eventmeta)
        continue
      p = self.participation_map[k]
      if 'horse' in k and (not p.horse or (self.data[key] == "" and p.horse != None) or p.horse.id != int(self.data[key])):
        if self.data[key] == "":
          p.horse = None
        else:
          p.horse = self.fields[k].queryset.get(id=self.data[key])
        self.participation_changed(p)
      if 'note' in k:
        p.note = unicode(self.data[key])
        self.participation_changed(p)
      if 'state' in k:
        p.state = int(self.data[key])
        self.participation_changed(p)
      if 'participant' in k and 'selector' not in k:
        val = self.data[key].split()
        f = []
        selkey = 'selector-%s' % key
        tryget=True

        if self.data[key].isdigit():
          f.append(Q(pk=int(self.data[key])))
        elif selkey in self.data and self.data[selkey].isdigit():
          f.append(Q(pk=int(self.data[selkey])))
        else:
          for v in val:
            f.append((Q(user__first_name__icontains=v) | Q(user__last_name__icontains=v)))

        if tryget:
          try:
            p.participant = UserProfile.objects.get(reduce(operator.and_, f))
          except MultipleObjectsReturned:
            self._handle_name_error(key, UserProfile.objects.filter(reduce(operator.and_, f)))
          except ObjectDoesNotExist:
            self.errors['__all__'] = self.error_class([_('You must choose a rider')])
            self.errors[key] = self.error_class([mark_safe(_('No such rider found. %sAdd one%s') % (('<a href="%s?orig=%s" target="_blank">' % (reverse('add_user'), self.data[key])), '</a>'))])
        self.participation_changed(p)
    for p in [ pp for pp in self.changed_participations if isinstance(pp, Participation) ]:
      if not p.participant.id:
        self.errors['__all__'] = self.error_class([_('You must choose a rider')])
        key = self.get_key(p.event.course_set.all()[0], p, 'participant')
        if not key in self.errors:
          self.errors[key] = self.error_class([_('This field is required')])

  def _handle_name_error(self, key, queryset):
    key = 'selector-%s' % key
    self._errors[key] = self.error_class([_("Please select rider")])
    self._errors['__all__'] = self.error_class([_("There was unambiguous riders")])
    participant_field = forms.ModelChoiceField(queryset=queryset, required=True)
    self.fields[key] = participant_field

  def participation_changed(self, part):
    if self.part_hash(part) not in self.already_changed:
      self.changed_participations.append(part)
      self.already_changed.add(self.part_hash(part))
  
  def add_field(self, course, participation, name, field):
    key = self.get_key(course, participation, name)
    self.fields[key] = field
    self.participation_map[key] = participation
    if (not self.participation_map.has_key(self.part_hash(participation))):
      self.participation_map[self.part_hash(participation)] = set()
    self.participation_map[self.part_hash(participation)].add(key)
    return key

  def part_hash(self, part):
    return '%sCC%sSS%sEE%s' % (part.participant.id, part.event.id, part.start, part.end)

  def get_key(self, course, participation, name):
    key_id = 'c%s_r%s_s%s_e%s_%s' % (course.id, participation.participant.id, participation.start.isoformat(), participation.end.isoformat(), name)
    return key_id

  def get_new_key(self, course, occurrence, name):
    return 'c%s_new_s%s_e%s_%s' % (course.id, occurrence.start.isoformat(), occurrence.end.isoformat(), name)

  def as_table(self):
    output = []
    # THEAD
    output.append('<thead>')
    output.append('<th></th>')
    _s = self.monday
    while (_s <= self.monday+datetime.timedelta(days=6)):
      output.append('<th>%s</th>' % format_date(_s, 'EE dd.MM', locale=get_language()))
      _s = _s + datetime.timedelta(days=1)
    output.append('</thead>')
    # TBODY
    output.append('<tbody>')
    for start_hour, weekdays in self.timetable.items():
      output.append('<tr><th>%s</th>' % start_hour)
      for day, cops in weekdays.items():
        output.append('<td>')
        for cop in cops:
          output.append('<span>')
          output.append('<a href="%s">' % cop[0].get_absolute_url())
          output.append(cop[0].name)
          output.append('</a>')
          output.append('</span>')
          output.append(unicode(self['c%s_s%s_e%s_instructor' % (cop[0].id, cop[1].start.isoformat(), cop[1].end.isoformat())]))
          output.append(unicode(self['c%s_s%s_e%s_notes' % (cop[0].id, cop[1].start.isoformat(), cop[1].end.isoformat())]))
          output.append('<ul>')
          hiding = False
          for part in cop[2]:
            output.append('<li')
            if hiding:
              output.append(' class="hiddable"')
            output.append('>')
            for field in part:
              if not field: continue
              if 'r0' in field:
                hiding = True
              if 'participant' in field and 'selector-%s' % field in self.fields:
                output.append(self[field].as_hidden())
                field = 'selector-%s' % field
              if self._errors and field in self._errors:
                output.append(unicode(self._errors[field]))
              output.append(unicode(self[field]))
            output.append('</li>')
          output.append('</ul>')
        output.append('</td>')
      output.append('</tr>')
    output.append('</tbody>')
    return mark_safe(u'\n'.join(output))

@permission_required('stables.change_participation')
def dashboard(request, week=None):
    if week == None:
        week = datetime.date.today().isocalendar()[1]
    week = int(week)
    # Default year is now
    year = int(request.GET.get('year', datetime.date.today().year))
    mon = datetime.datetime(*(Week(year, week).monday().timetuple()[:6]))
    courses = Course.objects.exclude(end__lt=mon).annotate(start_hour=Max('events__start')).order_by('-start_hour')
    horses = Horse.objects.exclude(last_usage_date__lt=mon)
    if request.method == 'POST':
      form = DashboardForm(request.POST, week=week, year=year, courses=courses, horses=horses)
      if form.is_valid():
        for p in form.changed_participations:
          p.save()
        for p in form.deleted_participations:
          p.delete()
        return redirect('%s?%s' % (request.path, request.GET.urlencode()))
    else:
      form = DashboardForm(week=week, year=year, courses=courses, horses=horses)

    return render_response(request, 'stables/dashboard.html', { 'week': week, 'form': form })

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

@permission_required('stables.add_accident')
def report_accident(request):
    acc = Accident()
    pid = request.GET.get('participation_id')
    if 'participation_id' in request.GET:
      p = Participation.objects.get(id=pid)
      acc.at = p.start
      acc.rider = p.participant.rider
      if p.horse:
        acc.horse = p.horse
      ins = list(InstructorParticipation.objects.filter(start=p.start, end=p.end, event=p.event)[:1])
      if ins:
        acc.instructor = ins[0].instructor.instructor
    if request.method == 'POST':
      form = AccidentForm(request.POST)
    else:
      form = AccidentForm(instance=acc)
    if form.is_valid():
      accident = form.save()
      redir = "%s"
      if pid:
        redir = redir+("?participation_id=%s" % pid)
      redir = redir % reverse('stables.views.report_accident_done', kwargs={'id': accident.id})
      return redirect(redir)
    return render_response(request, 'stables/accident/index.html', { 'form': form })

def report_accident_done(request, id):
    pid = request.GET.get('participation_id')
    redir = '/'
    if pid:
      redir = reverse('stables.views.widget_user', kwargs={'pid': pid})
    accident = Accident.objects.get(pk=id)
    return render_response(request, 'stables/accident/done.html', { 'accident': accident, 'return': redir })

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
            part.saldo = financial._count_saldo(transbypart[part])[0]
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

@permission_required('stables.view_transaction')
def widget_user(request, pid):
    part = Participation.objects.get(pk=pid)
    unused_tickets = part.participant.rider.unused_tickets
    transactions = list(Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id=part.id).order_by('object_id', 'created_on').prefetch_related('ticket_set'))

    setattr(part, 'transactions', [])
    setattr(part, 'saldo', 0)
    setattr(part, 'ticket_used', None)
    setattr(part, 'tickets', set())

    for ut in unused_tickets:
      part.tickets.add(ut.type)

    for t in transactions:
        if t.ticket_set.count() == 1:
            part.ticket_used=t.ticket_set.all()[0]
            part.tickets.discard(part.ticket_used.type)
        part.transactions.append(t)
    part.saldo = part.get_saldo()[0]

    return render_response(request, 'stables/widget_user.html', { 'p': part })

class TransactionsForm(forms.Form):
    transactions = []
    deleted_transactions = []

    def __init__(self, *args, **kwargs):
      transactions = kwargs.pop('transactions')
      unused_tickets = kwargs.pop('unused_tickets')
      self.participation = kwargs.pop('participation')
      super(TransactionsForm, self).__init__(*args, **kwargs)

      self._init_data(transactions, unused_tickets)

    def _post_clean(self):
      used_tickets = {}
      for (k, value) in self.cleaned_data.items():
        tvar, tid = k.split('_')
        tid = int(tid)
        if tvar == 'delete':
          if value:
            self.deleted_transactions.append(self.transactions[tid])
          continue
        if tvar == 'ticket':
          if value != '' and int(value) not in self.tickets:
            self._errors[k] = self.error_class([_('Invalid ticket id, choose from the list')])
          if value != '':
            used_tickets[int(value)] = self.transactions[tid]
          continue
        if tvar == 'created':
          tvar = 'created_on'
        setattr(self.transactions[tid], tvar, value)
      for (tid, t) in self.tickets.items():
        if tid in used_tickets:
          t.transaction = used_tickets[tid]
        else:
          t.transaction = None

    def save(self, *args, **kwargs):
      for (tid, t) in self.tickets.items():
        if t.transaction in self.deleted_transactions:
          t.transaction = None
      for (tid, t) in self.transactions.items():
        if t in self.deleted_transactions:
          self.deleted_transactions.remove(t)
          t.delete()
        elif t.amount:
          if tid == 0:
            t.customer = self.participation.participant.rider.customer
            t.source = self.participation
          t.save()
      for (tid, t) in self.tickets.items():
        if t.transaction:
          # Update the transaction from db
          t.transaction = Transaction.objects.get(pk=t.transaction.id)
        t.save()

    def _init_data(self, transactions, unused_tickets):
      self.transactions = dict(((lambda a: a.id)(v), v) for v in transactions)
      self.tickets = dict(((lambda a: a.id)(v), v) for v in unused_tickets)
      self.transactions[0] = Transaction()
      for (tid, t) in self.transactions.items():
        self.fields['delete_%s' % tid] = forms.BooleanField(required=False)
        self.fields['amount_%s' % tid] = forms.CharField(initial=t.amount, required=tid != 0)
        self.fields['created_%s' % tid] = forms.DateTimeField(initial=t.created_on)
        initial_ticket = None
        if tid != 0 and len(t.ticket_set.all()) > 0:
          initial_ticket = t.ticket_set.all()[0]
          self.tickets[initial_ticket.id] = initial_ticket
          initial_ticket = initial_ticket.id
        self.fields['ticket_%s' % tid] = forms.CharField(initial=initial_ticket, required=False)

    def as_table(self):
      output = []
      output.append('<thead>')
      output.append('<tr>')
      output.append('<th>Id</th>')
      output.append('<th>Amount</th>')
      output.append('<th>Ticket</th>')
      output.append('<th>Time</th>')
      output.append('<th>Delete</th>')
      output.append('</thead>')
      output.append('<tbody>')
      for (id, t) in sorted(self.transactions.items(), key=lambda a: a[0], reverse=True):
        output.append('<tr>')
        output.append('<td>%s</td>' % (t.id if t.id != None else ugettext("New")))
        self._print_td('amount_%s' % id, output)
        self._print_td('ticket_%s' % id, output)
        self._print_td('created_%s' % id, output)
        self._print_td('delete_%s' % id, output)
        output.append('</tr>')
      output.append('</tbody>')
      return mark_safe(u'\n'.join(output))

    def _print_td(self, field, output):
      output.append('<td>')
      if self._errors and field in self._errors:
        output.append(unicode(self._errors[field]))
      output.append('%s' % unicode(self[field]))
      output.append('</td>')

@permission_required('stables.add_transaction')
def modify_transactions(request, pid):
    part = Participation.objects.get(pk=pid)
    unused_tickets = part.participant.rider.unused_tickets
    transactions = list(Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id=part.id).order_by('object_id', 'created_on').prefetch_related('ticket_set'))

    setattr(part, 'transactions', [])
    setattr(part, 'saldo', 0)
    setattr(part, 'ticket_used', None)
    setattr(part, 'tickets', set())

    if request.method == 'POST':
      form = TransactionsForm(request.POST, transactions=transactions, unused_tickets=unused_tickets,  participation=part)
      if form.is_valid():
        form.save()
        return redirect('%s?%s' % (request.path, request.GET.urlencode()))
    else:
      form = TransactionsForm(transactions=transactions, unused_tickets=unused_tickets,  participation=part)

    return render_response(request, 'stables/modify_transactions.html', { 'form': form, 'tickets': form.tickets.values(), 'pid': pid })

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
        return User.objects.filter(username=username)[0].get_profile()
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

def view_user(request, username=None):
    if username:
        if (request.user.is_staff or username == request.user.username):
            user = User.objects.filter(username=username)[0]
        else:
            raise Http404
    else:
        user = request.user
    user = user.get_profile()

    setattr(user, 'next', [])
    if user.rider:
        user.next.append(Participation.objects.get_next_participation(user))

    if user.customer:
        setattr(user, 'transactions', Transaction.objects.filter(
          customer=user.customer, active=True).order_by('-created_on')[:request.GET.get('tmore', 5)])
        setattr(user, 'participations', Participation.objects.filter(participant__in=user.customer.riderinfo_set.values_list('user', flat=True), start__lte=datetime.datetime.now()).order_by('-start')[:request.GET.get('pmore', 5)])
        setattr(user, 'tickets', user.customer.unused_tickets)
        setattr(user, 'saldo', user.customer.saldo)
        for rdr in user.customer.riderinfo_set.all():
          if rdr.user != user:
            user.next.append(Participation.objects.get_next_participation(rdr.user))
    elif user.rider:
        setattr(user, 'participations', Participation.objects.filter(
          participant=user).order_by('-start')[:request.GET.get('pmore', 5)])
        setattr(user, 'tickets', user.rider.unused_tickets)

    if hasattr(user, 'tickets'):
      ticketamount = defaultdict(int)
      ticketexp = dict()
      for t in user.tickets:
        ticketamount[t.type] = ticketamount[t.type] + 1
        ticketexp[t.type] = t.expires if not t.type in ticketexp or ticketexp[t.type] > t.expires else ticketexp[t.type]
      user.tickets = dict()
      for tt in ticketexp.keys():
        user.tickets[tt] = (ticketamount[tt], ticketexp[tt])

    return render(request, 'stables/user/index.html', { 'user': user })

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
      self.fields['rider_id_'+str(p.participant.id)] = MyModelChoiceField(queryset=horses, label=str(p.participant), initial=p.horse, required=False)

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
        orig_start=occurrence.start
        orig_end=occurrence.end
        new_start=form.cleaned_data['new_start']
        new_end=form.cleaned_data['new_end']
        occurrence.move(new_start, new_end)
        Participation.objects.move(course, (orig_start, new_start), (orig_end, new_end))
        EventMetaData.objects.move(course, (orig_start, new_start), (orig_end, new_end))
        InstructorParticipation.objects.move(course, (orig_start, new_start), (orig_end, new_end))
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

from stables.models import TicketForm
@permission_required('stables.add_ticket')
def add_tickets(request, username):
  user = get_object_or_404(UserProfile, user__username=username)
  if user.rider:
    tf = TicketForm(initial={
      'owner_id': user.rider.id,
      'owner_type': ContentType.objects.get_for_model(RiderInfo)
      })
  else:
    tf = TicketForm(initial={
      'owner_id': user.customer.id,
      'owner_type': ContentType.objects.get_for_model(CustomerInfo),
      'to_customer': True
      })
    tf.fields['to_customer'].widget.attrs['disabled'] = 'disabled'
  if request.method == "POST":
    tf = TicketForm(request.POST)
    if tf.is_valid():
      tf.save_all()
      return redirect('stables.views.view_user', username)
  return render(request, 'stables/addtickets.html', { 'form': tf, 'user': user, 'username': username })


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

class MyModelChoiceIterator(forms.models.ModelChoiceIterator):
    """note that only line with # *** in it is actually changed"""
    def __init__(self, field):
        forms.models.ModelChoiceIterator.__init__(self, field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for obj in self.queryset: # ***
                yield self.choice(obj)


class MyModelChoiceField(forms.ModelChoiceField):
    """only purpose of this class is to call another ModelChoiceIterator"""
    def __init__(*args, **kwargs):
        forms.ModelChoiceField.__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        if hasattr(obj, 'nickname'):
            return obj.nickname
        return unicode(obj)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return MyModelChoiceIterator(self)

    choices = property(_get_choices, forms.ModelChoiceField._set_choices)
