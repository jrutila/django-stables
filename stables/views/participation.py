# coding=utf-8
import datetime

from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template import RequestContext
from django.views.generic import DetailView, View
from django.views.generic import TemplateView
from django.views.generic import CreateView, DeleteView
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from dateutil import parser
from schedule.models import Event

from stables.models.accident import Accident
from stables.models.financial import Ticket
from stables.models import CANCELED, ATTENDING, RESERVED
from stables.models.common import Transaction
from stables.models.course import Enroll
from stables.models.participations import Participation, InstructorParticipation
from stables.views import confirm_required
from stables.views.dashboard import DashboardMixin

def get_participation(request, **kwargs):
    if 'event' in kwargs:
        d = parser.parse(kwargs['start'])
        d = timezone.get_current_timezone().localize(d)
        ev = Event.objects.get(pk=kwargs['event'])
        occ = ev.get_occurrence(d)

        try:
            return Participation.objects.get_participation(request.user.userprofile, occ)
        except Participation.DoesNotExist:
            raise Http404('No %s matches the given query.' % Participation._meta.object_name)
    elif 'pk' in kwargs:
        return get_object_or_404(Participation, pk=kwargs['pk'], participant__user=request.user)

def cancel_ctx(request, **kwargs):
    part = get_participation(request, **kwargs)
    return RequestContext(request, { 'msg': u"Oletko varma, että haluat peruuttaa tapahtuman "+unicode(part), 'return_url': '/' })

class CancelView(View):
    @confirm_required('stables/confirm/confirm.html', cancel_ctx)
    def dispatch(self, request, *args, **kwargs):
        part = get_participation(request, **kwargs)

        if (CANCELED in part.get_possible_states()):
            part.cancel()
        else:
            raise AttributeError
        return redirect('/u/') # TODO: Fix me

from django.utils import formats
def attend_ctx(request, pk):
    part = get_object_or_404(Participation, pk=pk, participant__user=request.user)
    return RequestContext(request, { 'msg':
                                         u"Oletko varma, että haluat osallistua tapahtumaan %s %s %s"
                                         % (part.event.title,
                                            formats.date_format(part.get_occurrence().start),
                                            formats.time_format(part.get_occurrence().start)),
                                     'return_url': '/' })

class AttendView(View):
    @confirm_required('stables/confirm/confirm.html', attend_ctx)
    def dispatch(self, request, *args, **kwargs):
        kwargs['participant__user'] = request.user
        part = get_object_or_404(Participation, **kwargs)
        states = part.get_possible_states()
        if ATTENDING in states or RESERVED in states:
            part.attend()
        else:
            raise AttributeError
        return redirect('/u/') # TODO: Fix me

class CreateEnroll(DashboardMixin, CreateView):
    model = Enroll
    template_name = 'stables/generic_form.html'

class DeleteEnroll(DashboardMixin, DeleteView):
    model = Enroll
    template_name = 'stables/generic_form.html'

class ParticipationView(DashboardMixin, DetailView): # widget_user(request, pid):
    model = Participation
    template_name = 'stables/participation/participation.html'

    def get_object(self, queryset=None):
        part = Participation.objects.get(pk=self.kwargs.get(self.pk_url_kwarg, None))
        unused_tickets = Ticket.objects.get_unused_tickets(part.participant.rider, part.start)
        transactions = list(Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id=part.id).order_by('object_id', 'created_on').prefetch_related('ticket_set'))
        accidents = Accident.objects.filter(at__lte=part.end, at__gte=part.start, rider=part.participant.rider)

        setattr(part, 'transactions', [])
        setattr(part, 'saldo', 0)
        setattr(part, 'ticket_used', None)
        setattr(part, 'tickets', set())
        crs = part.event.course_set.all()
        setattr(part, 'course', crs[0] if crs else None)
        setattr(part, 'accidents', accidents)

        for ut in unused_tickets:
          part.tickets.add(ut.type)

        for t in transactions:
            if t.ticket_set.count() == 1:
                part.ticket_used=t.ticket_set.all()[0]
                part.tickets.discard(part.ticket_used.type)
            part.transactions.append(t)
        part.saldo = part.get_saldo()[0]

        return part

class DailyView(TemplateView):
    template_name = 'stables/daily.html'

    def get_context_data(self, **kwargs):
        ctx = super(TemplateView, self).get_context_data(**kwargs)
        date = datetime.datetime.strptime(kwargs['date'], '%Y-%m-%d').date()
        ctx['date'] = date
        start = datetime.datetime.combine(date, datetime.time.min)
        end = datetime.datetime.combine(date, datetime.time.max)
        tz = timezone.get_current_timezone()
        start = tz.localize(start)
        end = tz.localize(end)

        partids, parts = Participation.objects.generate_participations(start, end)
        instr = list(InstructorParticipation.objects.filter(start__gte=start, end__lte=end))
        instr = dict((i.event.pk, i) for i in instr)
        ticketcounts = Ticket.objects.get_ticketcounts(partids, limit=None)
        ctx['events'] = []
        for p in sorted(parts):
            for part in p[2]:
                if part.id in ticketcounts:
                    setattr(part, 'ticketcount', ticketcounts[part.id])
                else:
                    setattr(part, 'ticketcount', 0)
            ctx['events'].append((p[0],p[1],sorted(p[2], key=lambda x: x.state)))
        return ctx
