from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Q
from django.forms import Form
from django.views.generic.edit import UpdateView, FormView
from django.views.generic.edit import CreateView
from django.views.generic import ListView, RedirectView, View
from django.views.generic import DetailView
from django.contrib.auth.models import User
#from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from collections import defaultdict
from stables.forms.user import UserProfileForm
from stables.models import CANCELED
from stables.models.common import Transaction
from stables.models.participations import Participation
from stables.models.user import CustomerInfo, UserProfile
from django.core.urlresolvers import reverse

from django.contrib.auth.decorators import permission_required, login_required
from django.utils.decorators import method_decorator
#from stables_shop.models import TicketProductActivator
from stables_shop.models.activator import TicketProductActivator


class UserEditorMixin(object):
    @method_decorator(permission_required('stables.change_userprofile'))
    def dispatch(self, request, *args, **kwargs):
        return super(UserEditorMixin, self).dispatch(request, *args, **kwargs)

class HybridView(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if (request.user.is_staff):
            return ListUser.as_view()(request, *args, **kwargs)
        else:
            kwargs["username"] = request.user.username;
            return PlainViewUser.as_view()(request, *args, **kwargs)

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

class ActivateUser(FormView):
    form_class = Form

    def form_valid(self, form):
        user = User.objects.filter(username=self.kwargs['username'])[0]
        user.is_active = True
        user.save()
        return super(ActivateUser, self).form_valid(form)

    def get_success_url(self):
        return reverse('view_user', kwargs=self.kwargs)


class PlainViewUser(DetailView):
    template_name = 'stables/user/index.html'
    model = UserProfile

    def get_context_data(self, **kwargs):
        ctx = super(PlainViewUser, self).get_context_data(**kwargs)
        pmore = int(self.request.GET.get('pmore', 5))
        ctx["pmore"] = pmore
        return ctx

    def get_object(self, *args, **kwargs):
        user = User.objects.filter(username=self.kwargs['username'])[0]
        user = user.userprofile
        #CustomerInfo.objects.filter(id=user.customer.id).prefetch_related('transaction_set', 'transaction_set__ticket_set')
        pmore = int(self.request.GET.get('pmore', 5))
        tmore = int(self.request.GET.get('tmore', 3))

        setattr(user, 'next', [])

        # Set Orders
        if user.rider:
            nxt = Participation.objects.get_next_participation(user, limit=tmore)
            user.next = nxt
            tcks = TicketProductActivator.objects.filter(rider=user.rider).order_by("-order__created_at").prefetch_related("order", "order__items", "order__customer")
            ordrs = set()
            ordrs_add = ordrs.add
            o = [ t.order for t in tcks if not (t.order in ordrs or ordrs_add(t.order)) ]
            setattr(user, 'orders', o)

        # Set participations
        if user.rider.customer == user.customer:
            # This is the main account
            allriders = user.customer.riderinfo_set.values_list('user', flat=True)

            with connection.cursor() as nc:
                nc.execute("SELECT tr.object_id, sum(tr.amount) "
                           "from "
                           "stables_transaction tr "
                           "left outer join stables_ticket ti on ti.transaction_id = tr.id "
                           "inner join stables_participation p on p.id = tr.object_id "
                           "WHERE "
                           "ti.id IS NULL "
                           "AND tr.content_type_id = %s "
                           "AND tr.active = True "
                           "AND p.participant_id IN %s "
                           "AND p.state != %s"
                           "GROUP BY tr.object_id "
                           "HAVING SUM(tr.amount) != 0 ",
                           [ContentType.objects.get_for_model(Participation).id,
                            tuple(allriders),
                            CANCELED] )
                neg_parts = dict(nc.fetchall())

            #setattr(user, 'transactions', Transaction.objects.filter(
              #customer=user.customer, active=True)
              #.order_by('-created_on').select_related()[:tmore])
            parts = Participation.objects.filter(
              participant__in=allriders, start__lte=datetime.now()
            ).order_by('-start').select_related()[:pmore]

            np = Participation.objects.filter(
            id__in=neg_parts.keys()).order_by('-start').select_related()

            parts = sorted(list(parts)+list(np), key= lambda p: p.start, reverse=True)
            seen = set()
            seen_add = seen.add
            parts = [x for x in parts if not (x.id in seen or seen_add(x.id))]

            for p in parts:
                if p.id in neg_parts:
                    p.saldo = neg_parts[p.id]

            setattr(user, 'participations', parts)

            setattr(user, 'tickets', user.customer.unused_tickets)
            setattr(user, 'expired_tickets', user.customer.expired_tickets)

            setattr(user, 'saldo', user.customer.saldo)

            for rdr in user.customer.riderinfo_set.all():
                if rdr.user != user:
                    nxt = Participation.objects.get_next_participation(rdr.user, limit=tmore)
                    user.next.extend(nxt)

        elif user.rider:
            setattr(user, 'participations', Participation.objects.filter(
              participant=user).order_by('-start').select_related()[:pmore])
            setattr(user, 'tickets', user.rider.unused_tickets)
            setattr(user, 'expired_tickets', user.rider.expired_tickets)

        # Set tickets
        for attr in ['tickets', 'expired_tickets']:
            if hasattr(user, attr):
              ticketamount = defaultdict(int)
              ticketexp = dict()
              ticketfm = dict()
              for t in getattr(user, attr).prefetch_related('type'):
                ticketamount[t.type] = ticketamount[t.type] + 1
                ticketexp[t.type] = t.expires if not t.type in ticketexp or ticketexp[t.type] is None or (t.expires and ticketexp[t.type] > t.expires) else ticketexp[t.type]
                ticketfm[t.type] = t.is_family
              setattr(user, attr, dict())
              for tt in ticketexp.keys():
                getattr(user, attr)[tt] = (ticketamount[tt], ticketexp[tt], ticketfm[tt])

        return user

class ViewUser(UserEditorMixin, PlainViewUser):
    template_name = 'stables/user/index.html'
    model = UserProfile

    def get_object(self, *args, **kwargs):
        return super(ViewUser, self).get_object(*args, **self.kwargs)

class ListUser(UserEditorMixin, ListView):
    model = UserProfile
    template_name = 'stables/user/userprofile_list.html'

    def get_queryset(self):
        query = """select p.*, SUM(CASE WHEN ti.id IS NULL THEN tr.amount ELSE 0.00 END) as saldo FROM
                stables_userprofile p
                INNER JOIN auth_user u ON u.id = p.user_id
                LEFT OUTER JOIN stables_transaction tr ON tr.customer_id = p.customer_id AND tr.active = true
                LEFT OUTER JOIN stables_ticket ti ON ti.transaction_id = tr.id
                GROUP BY tr.customer_id, p.id, u.last_name ORDER BY u.last_name """
        from django.db.models.query import prefetch_related_objects
        raw_qs = UserProfile.objects.raw(query)
        raw_qs = list(raw_qs)
        prefetch_related_objects(raw_qs, ["user", ])
        return raw_qs
