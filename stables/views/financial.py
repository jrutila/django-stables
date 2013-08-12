from django.views.generic import FormView
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from stables.forms import TransactionsForm
from stables.forms import TicketForm
from stables.models import Participation
from stables.models import Transaction
from stables.models import UserProfile
from stables.models import RiderInfo
from stables.models import CustomerInfo

class EditTransactionsView(FormView):
    form_class = TransactionsForm
    template_name = 'stables/participation/modify_transactions.html'

    def get_form_kwargs(self):
        kwargs = super(FormView, self).get_form_kwargs()
        pid = self.kwargs['pid']
        part = Participation.objects.get(pk=pid)
        unused_tickets = part.participant.rider.unused_tickets
        transactions = list(Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id=part.id).order_by('object_id', 'created_on').prefetch_related('ticket_set'))
        kwargs['transactions'] = transactions
        kwargs['unused_tickets'] = unused_tickets
        kwargs['participation'] = part
        self.success_url = reverse('view_participation', kwargs={ 'pk': part.id })
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(FormView, self).form_valid(form)


class AddTicketsView(FormView):
    form_class = TicketForm
    template_name = 'stables/financial/addtickets.html'

    def dispatch(self, request, *args, **kwargs):
        self.success_url = reverse('view_user', kwargs=kwargs)
        return super(AddTicketsView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        user = get_object_or_404(UserProfile, user__username=self.kwargs['username'])

        if user.rider:
            return {
            'owner_id': user.rider.id,
            'owner_type': ContentType.objects.get_for_model(RiderInfo)
            }
        return {
            'owner_id': user.customer.id,
            'owner_type': ContentType.objects.get_for_model(CustomerInfo),
            'to_customer': True
            }


    def form_valid(self, form):
        form.save_all()
        return super(FormView, self).form_valid(form)
