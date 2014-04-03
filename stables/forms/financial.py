from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.safestring import mark_safe

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout, Fieldset, ButtonHolder

from stables.models import Transaction
from stables.models import Ticket

import datetime

class FinancialFormHelper(FormHelper):
    form_class = 'blueForms'
    form_method = 'post'


class TransactionsForm(forms.Form):
    transactions = []
    deleted_transactions = []

    def __init__(self, *args, **kwargs):
      transactions = kwargs.pop('transactions')
      unused_tickets = kwargs.pop('unused_tickets')
      self.participation = kwargs.pop('participation')
      super(TransactionsForm, self).__init__(*args, **kwargs)

      self._init_data(transactions, unused_tickets)

    def _post_clean(self):
      used_tickets = {}
      for (k, value) in self.cleaned_data.items():
        tvar, tid = k.split('_')
        tid = int(tid)
        if tvar == 'delete':
          if value:
            self.deleted_transactions.append(self.transactions[tid])
          continue
        if tvar == 'ticket':
          if value != '' and int(value) not in self.tickets:
            self._errors[k] = self.error_class([_('Invalid ticket id, choose from the list')])
          if value != '':
            used_tickets[int(value)] = self.transactions[tid]
          continue
        if tvar == 'created':
          tvar = 'created_on'
        setattr(self.transactions[tid], tvar, value)
      for (tid, t) in self.tickets.items():
        if tid in used_tickets:
          t.transaction = used_tickets[tid]
        else:
          t.transaction = None

    def save(self, *args, **kwargs):
      for (tid, t) in self.tickets.items():
        if t.transaction in self.deleted_transactions:
          t.transaction = None
      for (tid, t) in self.transactions.items():
        if t in self.deleted_transactions:
          self.deleted_transactions.remove(t)
          t.delete()
        elif t.amount:
          if tid == 0:
            t.customer = self.participation.participant.rider.customer
            t.source = self.participation
          t.save()
      for (tid, t) in self.tickets.items():
        if t.transaction:
          # Update the transaction from db
          t.transaction = Transaction.objects.get(pk=t.transaction.id)
        t.save()

    def _init_data(self, transactions, unused_tickets):
      self.transactions = dict(((lambda a: a.id)(v), v) for v in transactions)
      self.tickets = dict(((lambda a: a.id)(v), v) for v in unused_tickets)
      self.transactions[0] = Transaction()
      for (tid, t) in self.transactions.items():
        self.fields['delete_%s' % tid] = forms.BooleanField(required=False)
        self.fields['amount_%s' % tid] = forms.CharField(initial=t.amount, required=tid != 0)
        self.fields['created_%s' % tid] = forms.DateTimeField(initial=t.created_on)
        initial_ticket = None
        if tid != 0 and len(t.ticket_set.all()) > 0:
          initial_ticket = t.ticket_set.all()[0]
          self.tickets[initial_ticket.id] = initial_ticket
          initial_ticket = initial_ticket.id
        self.fields['ticket_%s' % tid] = forms.CharField(initial=initial_ticket, required=False)

    def as_table(self):
      output = []
      output.append('<thead>')
      output.append('<tr>')
      output.append('<th>Id</th>')
      output.append('<th>Amount</th>')
      output.append('<th>Ticket</th>')
      output.append('<th>Time</th>')
      output.append('<th>Delete</th>')
      output.append('</thead>')
      output.append('<tbody>')
      for (id, t) in sorted(self.transactions.items(), key=lambda a: a[0], reverse=True):
        output.append('<tr>')
        output.append('<td>%s</td>' % (t.id if t.id != None else ugettext("New")))
        self._print_td('amount_%s' % id, output)
        self._print_td('ticket_%s' % id, output)
        self._print_td('created_%s' % id, output)
        self._print_td('delete_%s' % id, output)
        output.append('</tr>')
      output.append('</tbody>')
      return mark_safe(u'\n'.join(output))

    def _print_td(self, field, output):
      output.append('<td>')
      if self._errors and field in self._errors:
        output.append(unicode(self._errors[field]))
      output.append('%s' % unicode(self[field]))
      output.append('</td>')

from django.contrib.contenttypes.models import ContentType
class EditTicketsForm(forms.Form):
    group = forms.ChoiceField(required=True)
    delete = forms.IntegerField(required=False, help_text=_("Amount of tickets to delete"))
    expires = forms.DateField(required=False, help_text=_("New expire date for selected tickets"))
    make_family = forms.BooleanField(required=False, help_text=_("Turn selected tickets to family tickets"))

    def __init__(self, *args, **kwargs):
          groups = kwargs.pop('groups')
          self.owner = kwargs.pop('owner')
          super(forms.Form, self).__init__(*args, **kwargs)
          self.fields['group'].choices = groups
          self.helper = FinancialFormHelper()
          self.helper.layout = Layout(
                HTML("""
                Choose one of actions: delete, change expire date or convert to family tickets
                    """),
                'group', 'delete', 'expires', 'make_family',
                ButtonHolder(
                  Submit('submit', 'Submit')
                  )
              )

    def save(self, *args, **kwargs):
        ot, tt, exp = self.cleaned_data['group'].split(':', 2)
        ot=ContentType.objects.get(id=ot)
        if ot.name == 'rider info':
            oid = self.owner.rider.id
        if ot.name == 'customer info':
            oid = self.owner.customer.id
        tickets = Ticket.objects.filter(
                type__id=tt,
                expires=exp,
                owner_id=oid,
                owner_type=ot).order_by('id').select_related('type')
        if self.cleaned_data['expires']:
            new_expires = datetime.datetime.combine(
                    self.cleaned_data['expires'], datetime.time(23,59,59))
            tickets.update(expires=new_expires)
        if ot.name == 'rider info' and self.cleaned_data['make_family']:
            for t in tickets:
                t.owner = self.owner.rider.customer
                t.save()
        if self.cleaned_data['delete']:
            for t in tickets[:self.cleaned_data['delete']]:
                t.delete()

class AddTicketsForm(forms.ModelForm):
    class Meta:
      model = Ticket
      exclude = ['transaction']
      widgets = {
          'owner_type': forms.HiddenInput(),
          'owner_id': forms.HiddenInput()
          }

    to_customer = forms.BooleanField(required=False, label=_('Family ticket'))
    amount = forms.IntegerField(required=True, initial=10, label=_('Amount'))
    expires = forms.DateField()

    def clean_expires(self):
        return datetime.datetime.combine(self.cleaned_data['expires'], datetime.time(23,59,59))

    def __init__(self, *args, **kwargs):
      super(AddTicketsForm, self).__init__(*args, **kwargs)
      self.helper = FinancialFormHelper()
      self.helper.layout = Layout(
            'type', 'expires', 'to_customer', 'amount', 'owner_type', 'owner_id', 'value',
            ButtonHolder(
              Submit('submit', 'Submit')
              )
          )

    def save_all(self):
      amnt = self.cleaned_data['amount']
      if (self.cleaned_data['to_customer']):
        self.instance.owner = self.instance.owner.customer
      for i in range(0, amnt):
        super(AddTicketsForm, self).save(commit=True)
        self.instance.id = None
