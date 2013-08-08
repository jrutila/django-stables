from django.views.generic import FormView
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from stables.forms import TransactionsForm
from stables.models import Participation
from stables.models import Transaction

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
