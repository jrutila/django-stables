import datetime
from decimal import Decimal

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _


__author__ = 'jorutila'


class CurrencyField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 10
        kwargs['decimal_places'] = 2
        models.DecimalField.__init__(self, *args, **kwargs)


class TicketType(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return self.name
    name = models.CharField(_("name"), max_length=32)
    description = models.TextField(_("description"))

class CustomerInfo(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        try:
            return self.user.__unicode__()
        except:
            return self.address
    address = models.CharField(max_length=500)
    ticket_warning_limit = 1


class Transaction(models.Model):
    class Meta:
        app_label = 'stables'
        permissions = (
            ('can_view_saldo', "Can see transactions and saldo"),
        )
    def __unicode__(self):
        #if self.source:
            #name = self.source.__unicode__()
        name = str(self.amount)
        if self.ticket_set.count():
          name = '(%s)' % str(self.ticket_set.all()[0].type)
        name = name + ': ' + str(self.source)
        return name
    active = models.BooleanField(default=True)
    customer = models.ForeignKey(CustomerInfo)
    amount = CurrencyField()
    created_on = models.DateTimeField(default = datetime.datetime.now)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    source = generic.GenericForeignKey('content_type', 'object_id')
    method = models.CharField(max_length=35, null=True, blank=True)

    def delete(self):
        self.ticket_set.clear()
        super(Transaction, self).delete()

    def getIncomeValue(self):
        if self.ticket_set.count() == 1:
            val = self.ticket_set.all()[0].value
            if val != None:
                return val
            return self.amount*-1
        if self.amount < 0:
            return Decimal('0.00')
        return self.amount

def _count_saldo(transactions):
    saldo = None
    ticket_used = None
    value = None
    if transactions:
        saldo = Decimal('0.00')
        value = abs(transactions[0].amount)
    for t in [t for t in transactions if t.active]:
      if t.ticket_set.count() == 0:
        saldo = saldo + t.amount
      elif t.ticket_set.count() > 0:
        ticket_used=t.ticket_set.all()[0]
    return (saldo, ticket_used, value)