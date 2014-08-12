# coding=utf-8
from django.shortcuts import redirect, get_object_or_404
from django.template import RequestContext
from django.views.generic import DetailView, FormView, View
from django.views.generic import TemplateView
from django.views.generic import CreateView, DeleteView
from django.contrib.contenttypes.models import ContentType
from stables.models import Enroll
from stables.models import Horse
from stables.models import InstructorInfo
from stables.models import Participation
from stables.models import Ticket
from stables.models import Transaction
from stables.models import Accident
from stables.models import InstructorParticipation
from stables.models import PARTICIPATION_STATES
from stables.models import CANCELED, ATTENDING, RESERVED
from stables.models import Course
from stables.views import LoginRequiredMixin, confirm_required
import datetime
from django.utils import timezone

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

class DashboardMixin(object):
    @method_decorator(permission_required('stables.change_participation'))
    def dispatch(self, request, *args, **kwargs):
        return super(DashboardMixin, self).dispatch(request, *args, **kwargs)

class Newboard(DashboardMixin, TemplateView):
    template_name = 'stables/newboard.html'

    def get_context_data(self, **kwargs):
        ctx = super(Newboard, self).get_context_data(**kwargs)
        ctx['states'] = (PARTICIPATION_STATES[0], PARTICIPATION_STATES[2], PARTICIPATION_STATES[3])
        ctx['horses'] = Horse.objects.all()
        ctx['instructors'] = [ i.user for i in InstructorInfo.objects.all().prefetch_related('user', 'user__user')]
        ctx['courses'] = Course.objects.exclude(end__lt=timezone.now()).prefetch_related('events')
        ctx['courses'] = sorted(ctx['courses'], key=lambda c: (c.lastEvent.start.weekday(), c.lastEvent.start.time()) if c.lastEvent else (None, None))
        return ctx

def cancel_ctx(request, id):
    part = get_object_or_404(Participation, pk=id, participant__user=request.user)
    return RequestContext(request, { 'msg': u"Oletko varma, että haluat peruuttaa tapahtuman "+part.__unicode__(), 'return_url': '/' })

class CancelView(View):
    @confirm_required('stables/confirm/confirm.html', cancel_ctx)
    def dispatch(self, request, *args, **kwargs):
        kwargs['participant__user'] = request.user
        part = get_object_or_404(Participation, **kwargs)
        if (CANCELED in part.get_possible_states()):
            part.cancel()
        else:
            raise AttributeError
        return redirect('/u/') # TODO: Fix me

def attend_ctx(request, id):
    part = get_object_or_404(Participation, pk=id, participant__user=request.user)
    return RequestContext(request, { 'msg': u"Oletko varma, että haluat osallistua tapahtumaan "+part.get_occurrence().__unicode__(), 'return_url': '/' })

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
        unused_tickets = part.participant.rider.unused_tickets
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
        for p in sorted(parts.items()):
            for part in p[1][1]:
                if part.id in ticketcounts:
                    setattr(part, 'ticketcount', ticketcounts[part.id])
                else:
                    setattr(part, 'ticketcount', 0)
            ctx['events'].append((p[0],p[1][0],sorted(p[1][1], key=lambda x: x.state)))
        return ctx
