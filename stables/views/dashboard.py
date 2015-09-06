from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from stables.models import PARTICIPATION_STATES
from stables.models.common import TicketType, Transaction
from stables.models.course import Course
from stables.models.horse import Horse
from stables.models.user import InstructorInfo

__author__ = 'jorutila'


class DashboardMixin(object):
    @method_decorator(login_required())
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('stables.change_participation'):
            return redirect('user_default')
        return super(DashboardMixin, self).dispatch(request, *args, **kwargs)


class Newboard(DashboardMixin, TemplateView):
    template_name = 'stables/dashboard/newboard.html'

    def get_context_data(self, **kwargs):
        ctx = super(Newboard, self).get_context_data(**kwargs)
        ctx['states'] = (PARTICIPATION_STATES[0], PARTICIPATION_STATES[1], PARTICIPATION_STATES[2], PARTICIPATION_STATES[3])
        ctx['horses'] = Horse.objects.all()
        ctx['instructors'] = [ i.user for i in InstructorInfo.objects.all().prefetch_related('user', 'user__user')]
        ctx['courses'] = Course.objects.all().prefetch_related('events') #exclude(end__lt=timezone.now())
        ctx['ticket_types'] = TicketType.objects.all();
        #ctx['courses'] = sorted(ctx['courses'], key=lambda c: (c.lastEvent.start.weekday(), c.lastEvent.start.time()) if c.lastEvent else (None, None))
        # TODO: Check that id db is PostgreSQL and take set away and add .distinct("method")
        ctx['pay_types'] = set(Transaction.objects.exclude(method__isnull=True).exclude(method="").values_list('method', flat=True))
        return ctx