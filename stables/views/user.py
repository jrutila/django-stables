from django.views.generic.edit import UpdateView
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from django.views.generic import DetailView
from django.contrib.auth.models import User
#from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from collections import defaultdict
from stables.models.user import CustomerInfo

from stables.forms import UserProfileForm
from stables.models import UserProfile
from stables.models import Participation
from stables.models import Transaction

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

class UserEditorMixin(object):
    @method_decorator(permission_required('stables.change_userprofile'))
    def dispatch(self, request, *args, **kwargs):
        return super(UserEditorMixin, self).dispatch(request, *args, **kwargs)

class EditUser(UserEditorMixin, UpdateView):
    template_name = 'stables/generic_form.html'
    form_class = UserProfileForm

    def get_object(self, **kwargs):
        return UserProfile.objects.filter(user__username=self.kwargs['username'])[0]

class AddUser(UserEditorMixin, CreateView):
    template_name = 'stables/generic_form.html'
    form_class = UserProfileForm

    def get_context_data(self, **kwargs):
        if self.request.GET.get('orig'):
            orig = self.request.GET.get('orig').split()
            form = kwargs['form']
            ff = ['first_name', 'last_name']
            for i in range(0, len(orig)):
                form.fields[ff[i]].initial = orig[i]
        return super(AddUser, self).get_context_data(**kwargs)

class ViewUser(UserEditorMixin, DetailView):
    template_name = 'stables/user/index.html'
    model = UserProfile

    def get_object(self, *args, **kwargs):
        user = User.objects.filter(username=self.kwargs['username'])[0]
        user = user.get_profile()
        CustomerInfo.objects.filter(id=user.customer.id).prefetch_related('transaction_set', 'transaction_set__ticket_set')
        pmore = self.request.GET.get('pmore', 5)
        tmore = self.request.GET.get('tmore', 5)

        setattr(user, 'next', [])
        if user.rider:
            user.next.append(Participation.objects.get_next_participation(user))

        if user.customer:
            setattr(user, 'transactions', Transaction.objects.filter(
              customer=user.customer, active=True)
              .order_by('-created_on').select_related()[:tmore])
            setattr(user, 'participations', Participation.objects.filter(
              participant__in=user.customer.riderinfo_set.values_list('user', flat=True), start__lte=datetime.now())
              .order_by('-start').select_related()[:pmore])
            setattr(user, 'tickets', user.customer.unused_tickets)
            setattr(user, 'expired_tickets', user.customer.expired_tickets)
            setattr(user, 'saldo', user.customer.saldo)
            for rdr in user.customer.riderinfo_set.all():
              if rdr.user != user:
                user.next.append(Participation.objects.get_next_participation(rdr.user))
        elif user.rider:
            setattr(user, 'participations', Participation.objects.filter(
              participant=user).order_by('-start').select_related()[:pmore])
            setattr(user, 'tickets', user.rider.unused_tickets)
            setattr(user, 'expired_tickets', user.rider.expired_tickets)

        for attr in ['tickets', 'expired_tickets']:
            if hasattr(user, attr):
              ticketamount = defaultdict(int)
              ticketexp = dict()
              for t in getattr(user, attr):
                ticketamount[t.type] = ticketamount[t.type] + 1
                ticketexp[t.type] = t.expires if not t.type in ticketexp or (t.expires and ticketexp[t.type] > t.expires) else ticketexp[t.type]
              setattr(user, attr, dict())
              for tt in ticketexp.keys():
                getattr(user, attr)[tt] = (ticketamount[tt], ticketexp[tt])

        return user

class ListUser(UserEditorMixin, ListView):
    model = UserProfile
    template_name = 'stables/user/userprofile_list.html'

    def get_queryset(self):
        query = """select p.*, SUM(CASE WHEN ti.id IS NULL THEN tr.amount ELSE 0.00 END) as saldo FROM
                stables_userprofile p
                LEFT OUTER JOIN stables_transaction tr ON tr.customer_id = p.customer_id AND tr.active = true
                LEFT OUTER JOIN stables_ticket ti ON ti.transaction_id = tr.id
                GROUP BY tr.customer_id, p.id """
        from django.db.models.query import prefetch_related_objects
        raw_qs = UserProfile.objects.raw(query)
        raw_qs = list(raw_qs)
        prefetch_related_objects(raw_qs, ["user", ])
        return raw_qs
