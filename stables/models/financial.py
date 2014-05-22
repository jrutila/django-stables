from django.db import models
from django.db.models import Q
from user import CustomerInfo, RiderInfo
import datetime
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from decimal import Decimal

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^stables\.models\.financial\.CurrencyField"])

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

class TicketManager(models.Manager):
    def get_ticketcounts(self, participations, limit=1):
        crs = connection.cursor()
        try:
            schema = connection.schema_name + "."
        except AttributeError:
            schema = ''
        if not participations:
            return dict()
        query = 'select p.id, count(t.id) from %(schema)sstables_participation p inner join %(schema)sstables_userprofile u on u.id = p.participant_id inner join %(schema)sstables_riderinfo r on r.id = u.rider_id inner join %(schema)sstables_ticket t on (r.customer_id = t.owner_id and owner_type_id = %(customer)d) or (u.rider_id = t.owner_id and t.owner_type_id = %(rider)d) where p.id in (%(partids)s) and t.transaction_id is null and t.expires >= p.start group by p.id' % { 'schema' : schema, 'customer': ContentType.objects.get_for_model(CustomerInfo).id, 'rider': ContentType.objects.get_for_model(RiderInfo).id, 'partids': ', '.join(list(map(lambda x: '%s', participations))) }
        if limit:
            query += " having count(t.id) <= %d" % limit
        crs.execute(query, list(participations))
        return dict(crs.fetchall())

class Ticket(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        s = self.type.__unicode__() + ' (' + unicode(self.owner) + ')'
        if isinstance(self.owner, CustomerInfo):
            s = s + " F "
        if self.transaction:
            s = s + "(USED)"
        return s
    objects = TicketManager()
    type = models.ForeignKey(TicketType, verbose_name=_("Ticket type"))
    owner_type = models.ForeignKey(ContentType)
    owner_id = models.PositiveIntegerField()
    owner = generic.GenericForeignKey('owner_type', 'owner_id')
    transaction = models.ForeignKey("Transaction", null=True, blank=True, related_name="ticket_set")
    expires = models.DateTimeField(_("Expires"), null=True, blank=True)
    value = CurrencyField(_("Value"), null=True, blank=True, help_text=_("Sell value of one ticket. Can be used when calculating user revenue."))

class TransactionActivator(models.Model):
    class Meta:
        app_label = 'stables'
        abstract = True

class ParticipationTransactionActivatorManager(models.Manager):
    def try_create(self, participation, fee, ticket_type=None):
        if self.filter(participation=participation).count() > 0:
            return
        part_type = ContentType.objects.get_for_model(participation)
        if Transaction.objects.filter(content_type__pk=part_type.id, object_id=participation.id).count() > 0:
            return
        # TODO: 24 to something right
        act = self.create(participation=participation, fee=fee, activate_before_hours=24)
        act.ticket_type = ticket_type
        act.try_activate()
        return act

def _use_ticket(ticket_query, transaction):
    tickets = ticket_query
    if tickets.count() > 0:
        ticket = tickets.order_by('expires')[0]
        ticket.transaction = transaction
        ticket.save()

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

def get_saldo(self):
    return _count_saldo(Transaction.objects.filter(active=True,
          content_type=ContentType.objects.get_for_model(self),
          object_id=self.id).prefetch_related('ticket_set'))

def get_customer_saldo(self):
    return _count_saldo(self.transaction_set.all())[0]

def _get_rider_q(self):
    qcustomer = Q(owner_type=ContentType.objects.get_for_model(self.customer), owner_id=self.customer.id)
    qrider = Q(owner_type=ContentType.objects.get_for_model(self), owner_id=self.id)
    return Q(qrider | qcustomer)

def _get_customer_q(self):
    qcustomer = Q(owner_type=ContentType.objects.get_for_model(self), owner_id=self.id)
    qrider = Q(owner_type=ContentType.objects.get_for_model(RiderInfo), owner_id__in=self.riderinfo_set.all())
    return Q(qrider | qcustomer)

def _get_valid_q():
    return Q(Q(expires__gte=datetime.datetime.now()) | Q(expires__isnull=True))

def _get_expired_q():
    return Q(expires__lt=datetime.datetime.now())

def _get_tickets(owner_q, expire_q):
    return Ticket.objects.filter(owner_q, transaction__isnull=True).filter(expire_q)

def _get_rider_valid_unused_tickets(self):
    return _get_tickets(_get_rider_q(self), _get_valid_q())

def _get_rider_expired_unused_tickets(self):
    return _get_tickets(_get_rider_q(self), _get_expired_q())

def _get_customer_valid_unused_tickets(self):
    return _get_tickets(_get_customer_q(self), _get_valid_q())

def _get_customer_expired_unused_tickets(self):
    return _get_tickets(_get_customer_q(self), _get_expired_q())

import participations
from participations import Course, Participation
Participation.get_saldo = get_saldo
RiderInfo.unused_tickets = property(_get_rider_valid_unused_tickets)
RiderInfo.expired_tickets = property(_get_rider_expired_unused_tickets)
CustomerInfo.unused_tickets = property(_get_customer_valid_unused_tickets)
CustomerInfo.expired_tickets = property(_get_customer_expired_unused_tickets)
CustomerInfo.saldo = property(get_customer_saldo)

from schedule.models import Event
def _get_default_fee(self):
    if self.course_set.count() > 0:
        return self.course_set.all()[0].default_participation_fee
    return Decimal('0.00')

Event.default_fee = property(_get_default_fee)

def pay_participation(participation, value=None, ticket=None):
    transactions = Transaction.objects.filter(
        active=True,
        content_type=ContentType.objects.get_for_model(participation),
        object_id=participation.id)
    customer = participation.participant.rider.customer

    if transactions.count() == 0:
        vval = value
        if vval == None and participation.event.course_set.count() > 0:
            vval = participation.event.default_fee
        t = Transaction.objects.create(
              active=True,
              content_type=ContentType.objects.get_for_model(Participation),
              object_id=participation.id,
              amount=-1*vval,
              customer=customer)

    if value != None and value != abs(transactions[0].amount):
        t = transactions[0]
        t.amount = -1*value
        t.save()

    saldo, ticket_used, value = _count_saldo(transactions)

    if ticket_used:
      ticket_used.transaction=None
      ticket_used.save()
      saldo, ticket_used, value = _count_saldo(transactions)

    if ticket:
        ticket = participation.participant.rider.unused_tickets.filter(type=ticket).order_by('expires')[0]
        ticket.transaction = transactions.filter(amount__lt=0)[0]
        ticket.save()
        for t in transactions[1:]:
            t.delete()

    elif saldo < 0:
        Transaction.objects.create(
          active=True,
          content_type=ContentType.objects.get_for_model(Participation),
          object_id=participation.id,
          amount=-1*saldo,
          customer=customer)

from django.utils import timezone
class ParticipationTransactionActivator(TransactionActivator):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return self.participation.__unicode__() + ': ' + str(self.fee)
    participation = models.ForeignKey(Participation)
    activate_before_hours = models.IntegerField()
    fee = CurrencyField()
    objects = ParticipationTransactionActivatorManager()
    ticket_type = models.ManyToManyField(TicketType, null=True, blank=True)

    def try_activate(self):
        if self.participation.start-datetime.timedelta(hours=self.activate_before_hours) < timezone.now():
            return self.activate()
        return None

    def activate(self):
        t = None
        if self.participation.state == participations.ATTENDING:
            t = Transaction()
            t.amount = self.fee*-1
            t.customer = self.participation.participant.rider.customer
            t.source = self.participation
            t.save()
            tickets = self.participation.participant.rider.unused_tickets.filter(type__in=self.ticket_type.all())
            _use_ticket(tickets, t)
        self.delete()
        return t

@receiver(post_save, sender=Participation)
def handle_Participation_save(sender, **kwargs):
    parti = kwargs['instance']
    # Only if the user is attending
    trans=Transaction.objects.filter(
        content_type=ContentType.objects.get_for_model(parti),
        object_id=parti.id
        )
    if parti.state == participations.ATTENDING:
        # If there is deactivated stuff
        trans = trans.filter(active=False)
        course = Course.objects.filter(events__in=[parti.event])
        if course:
            course = course[0]
            if trans:
              for t in trans:
                t.active=True
                t.save()
                if not Ticket.objects.filter(transaction=t).exists() and t.amount < 0:
                  tickets = parti.participant.rider.unused_tickets.filter(type__in=course.ticket_type.all())
                  _use_ticket(tickets, t)
            else:
              ParticipationTransactionActivator.objects.try_create(parti, course.default_participation_fee, course.ticket_type.all())
    elif parti.state == participations.CANCELED or parti.state == participations.RESERVED:
        ParticipationTransactionActivator.objects.filter(participation=parti).delete()
        trans.deactivate()
        for ticket in Ticket.objects.filter(transaction__in=trans):
          ticket.transaction = None
          ticket.save()

from participations import Enroll
class CourseTransactionActivator(TransactionActivator):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return str(self.enroll) + ": " + str(self.fee)
    enroll = models.ForeignKey(Enroll)
    fee = CurrencyField()

    def try_activate(self):
        t = Transaction()
        t.amount = self.fee*-1
        t.customer = self.enroll.rider.customer
        t.source = self.enroll
        t.save()
        self.delete()

class TransactionQuerySet(models.query.QuerySet):
  def deactivate(self):
    for t in self:
      t.active = False
      t.save()

class TransactionManager(models.Manager):
  def get_query_set(self):
    return TransactionQuerySet(self.model, using=self._db)

  def get_transactions(self, participations):
    return self.filter(active=True, content_type=ContentType.objects.get_for_model(Participation), object_id__in=participations).order_by('object_id', 'created_on').select_related().prefetch_related('ticket_set__type', 'ticket_set__owner')

  def get_saldos(self, participations):
      ret = {}
      trans = list(self.get_transactions(participations))
      ids = participations
      for (pid, tt) in [(x, [y for y in trans if y.object_id==x]) for x in ids]:
          ret[pid] = _count_saldo(tt)
      return ret

class Transaction(models.Model):
    objects = TransactionManager()
    class Meta:
        app_label = 'stables'
        permissions = (
            ('can_view_saldo', "Can see transactions and saldo"),
        )
    def __unicode__(self):
        #if self.source:
            #name = self.source.__unicode__() 
        name = unicode(self.amount)
        if self.ticket_set.count():
          name = '(%s)' % unicode(self.ticket_set.all()[0].type)
        name = name + ': ' + unicode(self.source)
        return name
    active = models.BooleanField(default=True)
    customer = models.ForeignKey(CustomerInfo)
    amount = CurrencyField()
    created_on = models.DateTimeField(default = datetime.datetime.now)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    source = generic.GenericForeignKey('content_type', 'object_id')
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
