from django.views.generic import FormView
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from stables.forms import TransactionsForm
from stables.forms import AddTicketsForm
from stables.forms import EditTicketsForm
from stables.models import Participation
from stables.models import Transaction
from stables.models import UserProfile
from stables.models import RiderInfo
from stables.models import CustomerInfo

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

class ParticipationMixin(object):
    @method_decorator(permission_required('stables.change_participation'))
    def dispatch(self, request, *args, **kwargs):
        return super(ParticipationMixin, self).dispatch(request, *args, **kwargs)

class EditTransactionsView(ParticipationMixin, FormView):
    form_class = TransactionsForm
    template_name = 'stables/participation/modify_transactions.html'

    def get_form_kwargs(self):
        kwargs = super(FormView, self).get_form_kwargs()
        pid = self.kwargs['pid']
        part = Participation.objects.get(pk=pid)
        self.unused_tickets = list(part.participant.rider.unused_tickets)
        transactions = list(Transaction.objects.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id=part.id).order_by('object_id', 'created_on').prefetch_related('ticket_set'))
        kwargs['transactions'] = transactions
        kwargs['unused_tickets'] = self.unused_tickets
        kwargs['participation'] = part
        self.success_url = reverse('view_participation', kwargs={ 'pk': part.id })
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(EditTransactionsView, self).get_context_data(**kwargs)
        ctx['tickets'] = self.get_form(self.form_class).tickets.values()
        return ctx

    def form_valid(self, form):
        form.save()
        return super(FormView, self).form_valid(form)

from collections import defaultdict
from django.contrib.auth.models import User

class EditTicketsView(ParticipationMixin, FormView):
    form_class = EditTicketsForm
    template_name = 'stables/generic_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.success_url = reverse('view_user', args=(self.kwargs['username'],))
        return super(EditTicketsView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(FormView, self).get_form_kwargs()
        user = User.objects.filter(username=self.kwargs['username'])[0].get_profile()
        kwargs['owner'] = user

        user = user.customer

        ticketamount = defaultdict(int)
        for attr in ['unused_tickets', 'expired_tickets']:
            if hasattr(user, attr):
              for t in getattr(user, attr):
                key = (t.owner, t.type, t.expires or None)
                ticketamount[key] = ticketamount[key] + 1
        kwargs['groups'] = []
        for ((owner, tt, exp), amnt) in ticketamount.items():
            key = "%d:%d:%s" % (ContentType.objects.get_for_model(owner).id, tt.id, exp.isoformat() if exp else None)
            kwargs['groups'].append(
                (key, "%s (%s) -  %d kpl %s" % (tt, exp, amnt, "(F)" if isinstance(owner, CustomerInfo) else ""))
                )
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(FormView, self).form_valid(form)

class AddTicketsView(ParticipationMixin, FormView):
    form_class = AddTicketsForm
    template_name = 'stables/generic_form.html'

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
