from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic import CreateView, DeleteView
from django.contrib.contenttypes.models import ContentType
from stables.models import Enroll
from stables.models import Horse
from stables.models import InstructorInfo
from stables.models import Participation
from stables.models import Transaction
from stables.models import Accident
from stables.models import PARTICIPATION_STATES

class Newboard(TemplateView):
    template_name = 'stables/newboard.html'

    def get_context_data(self, **kwargs):
        ctx = super(Newboard, self).get_context_data(**kwargs)
        ctx['states'] = (PARTICIPATION_STATES[0], PARTICIPATION_STATES[2], PARTICIPATION_STATES[3])
        ctx['horses'] = Horse.objects.all()
        ctx['instructors'] = [ i.user for i in InstructorInfo.objects.all().prefetch_related('user', 'user__user')]
        return ctx

class CreateEnroll(CreateView):
    model = Enroll
    template_name = 'stables/generic_form.html'

class DeleteEnroll(DeleteView):
    model = Enroll
    template_name = 'stables/generic_form.html'

class ParticipationView(DetailView): # widget_user(request, pid):
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
        setattr(part, 'course', part.event.course_set.all()[0])
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
