from django.views.generic import FormView
from datetime import date, datetime
from isoweek import Week
from django.db.models import Max
from django.core.urlresolvers import reverse

from stables.forms import DashboardForm
from stables.models import Course
from stables.models import Horse

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
