from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Q
from django.utils.translation import get_language

from babel.dates import format_date
import operator
from datetime import datetime, timedelta
from isoweek import Week

from stables.models import InstructorParticipation
from stables.models import InstructorInfo
from stables.models import Participation
from stables.models import EventMetaData
from stables.models import Accident
from stables.models import Transaction
from stables.models import UserProfile
from stables.models import ATTENDING
from stables.models import PARTICIPATION_STATES
from stables.models import financial


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
          reverse('view_participation', args=[self.participation.id])
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
    self.monday = datetime(*(Week(self.year, self.week).monday().timetuple()[:6]))
    self.sunday = self.monday+timedelta(days=6, hours=23, minutes=59)
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
        if o.cancelled:
            cop = (c, o, [], [])
            self.timetable[o.start.hour][o.start.weekday()].append(cop)
            continue
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
    while (_s <= self.monday+timedelta(days=6)):
      output.append('<th>%s</th>' % format_date(_s, 'EE dd.MM', locale=get_language()))
      _s = _s + timedelta(days=1)
    output.append('</thead>')
    # TBODY
    output.append('<tbody>')
    for start_hour, weekdays in self.timetable.items():
      output.append('<tr><th>%s</th>' % start_hour)
      for day, cops in weekdays.items():
        output.append('<td>')
        for cop in cops:
          stylespan = '<span'
          if cop[1].cancelled:
              stylespan = stylespan + ' class="cancelled"'
          stylespan = stylespan + '>'
          output.append(stylespan)
          output.append('<a href="%s">' % cop[0].get_absolute_url())
          output.append(cop[0].name)
          output.append('</a>')
          output.append('</span>')
          if cop[1].cancelled:
              continue
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
