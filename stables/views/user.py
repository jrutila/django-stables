from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from django.views.generic import ListView
from django.views.generic import DetailView
from django.http import HttpResponse
from django.contrib.auth.models import User
from datetime import datetime
from collections import defaultdict

from stables.forms import UserProfileAddForm
from stables.forms import UserProfileForm
from stables.models import UserProfile
from stables.models import Participation
from stables.models import Transaction

class EditUser(UpdateView):
    template_name = 'stables/user/edit_user.html'
    form_class = UserProfileForm

    def get_object(self, **kwargs):
        return UserProfile.objects.filter(user__username=self.kwargs['username'])[0]

class AddUser(FormView):
    template_name = 'stables/user/add_user.html'
    form_class = UserProfileAddForm

    def form_valid(self, form):
        form.save(commit = True)
        return HttpResponse('<script type="text/javascript">window.close()</script>Close this window.')

    def get_context_data(self, **kwargs):
        if self.request.GET.get('orig'):
            orig = self.request.GET.get('orig').split()
            form = kwargs['form']
            ff = ['first_name', 'last_name']
            for i in range(0, len(orig)):
                form.fields[ff[i]].initial = orig[i]
        return super(AddUser, self).get_context_data(**kwargs)

class ViewUser(DetailView):
    template_name = 'stables/user/index.html'
    model = UserProfile

    def get_object(self, *args, **kwargs):
        user = User.objects.filter(username=self.kwargs['username'])[0]
        user = user.get_profile()

        setattr(user, 'next', [])
        if user.rider:
            user.next.append(Participation.objects.get_next_participation(user))

        if user.customer:
            setattr(user, 'transactions', Transaction.objects.filter(
              customer=user.customer, active=True).order_by('-created_on')[:5])
            setattr(user, 'participations', Participation.objects.filter(participant__in=user.customer.riderinfo_set.values_list('user', flat=True), start__lte=datetime.now()).order_by('-start')[:5])
            setattr(user, 'tickets', user.customer.unused_tickets)
            setattr(user, 'saldo', user.customer.saldo)
            for rdr in user.customer.riderinfo_set.all():
              if rdr.user != user:
                user.next.append(Participation.objects.get_next_participation(rdr.user))
        elif user.rider:
            setattr(user, 'participations', Participation.objects.filter(
              participant=user).order_by('-start')[:5])
            setattr(user, 'tickets', user.rider.unused_tickets)

        if hasattr(user, 'tickets'):
          ticketamount = defaultdict(int)
          ticketexp = dict()
          for t in user.tickets:
            ticketamount[t.type] = ticketamount[t.type] + 1
            ticketexp[t.type] = t.expires if not t.type in ticketexp or ticketexp[t.type] > t.expires else ticketexp[t.type]
          user.tickets = dict()
          for tt in ticketexp.keys():
            user.tickets[tt] = (ticketamount[tt], ticketexp[tt])

        return user

class ListUser(ListView):
    model = UserProfile
    template_name = 'stables/user/userprofile_list.html'
