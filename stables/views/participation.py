from django.views.generic import FormView
from django.views.generic import DetailView
from django.views.generic import TemplateView
from datetime import date, datetime
from isoweek import Week
from django.db.models import Max
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from stables.forms import DashboardForm
from stables.models import Course
from stables.models import Horse
from stables.models import Participation
from stables.models import Transaction
from stables.models import PARTICIPATION_STATES

class Newboard(TemplateView):
    template_name = 'stables/newboard.html'

    def get_context_data(self, **kwargs):
        ctx = super(Newboard, self).get_context_data(**kwargs)
        ctx['states'] = PARTICIPATION_STATES
        ctx['horses'] = Horse.objects.all()
        return ctx

class Dashboard(FormView):
    template_name = 'stables/dashboard.html'
    form_class = DashboardForm

    def dispatch(self, request, *args, **kwargs):
        if 'week' in kwargs:
            self.week = int(kwargs.pop('week'))
            self.success_url = reverse('dashboard', kwargs={'week': self.week})
        else:
            self.success_url = reverse('dashboard')
            self.week = date.today().isocalendar()[1]
        self.year = int(request.GET.get('year', date.today().year))
        return super(Dashboard, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(Dashboard, self).get_form_kwargs()
        mon = datetime(*(Week(self.year, self.week).monday().timetuple()[:6]))
        kwargs['courses'] = Course.objects.exclude(end__lt=mon).annotate(start_hour=Max('events__start')).order_by('-start_hour')
        kwargs['week'] = self.week
        kwargs['horses'] = Horse.objects.exclude(last_usage_date__lt=mon)
        kwargs['year'] = self.year
        return kwargs

    def form_valid(self, form):
        for p in form.changed_participations:
          p.save()
        for p in form.deleted_participations:
          p.delete()
        return super(Dashboard, self).form_valid(form)

class ParticipationView(DetailView): # widget_user(request, pid):
    model = Participation
    template_name = 'stables/participation/participation.html'

    def get_object(self, queryset=None):
        part = Participation.objects.get(pk=self.kwargs.get(self.pk_url_kwarg, None))
        unused_tickets = part.participant.rider.unused_tickets
        transactions = list(Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id=part.id).order_by('object_id', 'created_on').prefetch_related('ticket_set'))

        setattr(part, 'transactions', [])
        setattr(part, 'saldo', 0)
        setattr(part, 'ticket_used', None)
        setattr(part, 'tickets', set())
        setattr(part, 'course', part.event.course_set.all()[0])

        for ut in unused_tickets:
          part.tickets.add(ut.type)

        for t in transactions:
            if t.ticket_set.count() == 1:
                part.ticket_used=t.ticket_set.all()[0]
                part.tickets.discard(part.ticket_used.type)
            part.transactions.append(t)
        part.saldo = part.get_saldo()[0]

        return part
