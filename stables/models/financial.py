import datetime
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from schedule.models import Event

from stables.models import ATTENDING, RESERVED, CANCELED, WAITFORPAY
from stables.models.common import CurrencyField, TicketType, Transaction, _count_saldo
from stables.models.course import Enroll
from stables.models.event_metadata import EventMetaData
from stables.models.participations import Participation
from stables.models.user import CustomerInfo, RiderInfo


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

    def get_unused_tickets(self, rider, dt):
        return _get_tickets(_get_rider_q(rider), _get_valid_q(dt))

class Ticket(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        s = unicode(self.type) + ' (' + unicode(self.owner) + ')'
        if isinstance(self.owner, CustomerInfo):
            s = s + " F "
        if self.transaction:
            s = s + "(USED)"
        return s
    objects = TicketManager()
    type = models.ForeignKey(TicketType, verbose_name=_("Ticket type"))
    owner_type = models.ForeignKey(ContentType)
    owner_id = models.PositiveIntegerField()
    owner = GenericForeignKey('owner_type', 'owner_id')
    transaction = models.ForeignKey("Transaction", null=True, blank=True, related_name="ticket_set")
    expires = models.DateTimeField(_("Expires"), null=True, blank=True)
    value = CurrencyField(_("Value"), null=True, blank=True, help_text=_("Sell value of one ticket. Can be used when calculating user revenue."))

    @property
    def is_family(self):
        return self.owner_type_id == ContentType.objects.get_for_model(CustomerInfo).id


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
        if ticket_type:
            act.ticket_type = ticket_type
        act.try_activate()
        return act

def _use_ticket(ticket_query, transaction):
    tickets = ticket_query
    if tickets.count() > 0:
        ticket = tickets.order_by('expires')[0]
        ticket.transaction = transaction
        ticket.save()

def get_saldo(self):
    return _count_saldo(Transaction.objects.filter(active=True,
          content_type=ContentType.objects.get_for_model(self),
          object_id=self.id).prefetch_related('ticket_set'))

def get_pay_transaction(self):
    return Transaction.objects.filter(active=True,
                                                   content_type=ContentType.objects.get_for_model(self),
                                                   object_id=self.id, amount__gt=0)[0]

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

def _get_valid_q(dt=None):
    return Q(Q(expires__gte=dt or datetime.datetime.now()) | Q(expires__isnull=True))

def _get_expired_q(dt=None):
    return Q(expires__lt=dt or datetime.datetime.now())

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

Participation.get_saldo = get_saldo
Participation.get_pay_transaction = get_pay_transaction
RiderInfo.unused_tickets = property(_get_rider_valid_unused_tickets)
RiderInfo.expired_tickets = property(_get_rider_expired_unused_tickets)
CustomerInfo.unused_tickets = property(_get_customer_valid_unused_tickets)
CustomerInfo.expired_tickets = property(_get_customer_expired_unused_tickets)
CustomerInfo.saldo = property(get_customer_saldo)

def _get_default_fee(self):
    if self.course_set.count() > 0:
        return self.course_set.all()[0].default_participation_fee
    return Decimal('0.00')

Event.default_fee = property(_get_default_fee)

def pay_participation(participation, value=None, ticket=None, method=None):
    transactions = Transaction.objects.filter(
        active=True,
        content_type=ContentType.objects.get_for_model(participation),
        object_id=participation.id)
    customer = participation.participant.rider.customer

    saldo, ticket_used, rvalue, method = _count_saldo(transactions)

    if ticket_used:
        ticket_used.transaction=None
        ticket_used.save()
        saldo, ticket_used, rvalue, method = _count_saldo(transactions)

    dvalue = value
    if dvalue == None and participation.event.course_set.count() > 0:
        dvalue = participation.event.default_fee
        saldo = -1*dvalue
    if value == None and ticket==None:
        value = -1*saldo
    if value != None and value < 0:
        dvalue = -1*value

    if transactions.count() > 0:
        if dvalue != None:
            transactions[0].amount = -1*dvalue
            transactions[0].save()
        for t in transactions[1:]:
            t.delete()
    else:
        t = Transaction.objects.create(
            active=True,
            content_type=ContentType.objects.get_for_model(Participation),
            object_id=participation.id,
            amount=-1*dvalue,
            customer=customer,
            method=method)

    saldo, ticket_used, rvalue, method = _count_saldo(transactions.all())

    if saldo != 0:
        if value != None and value > 0:
            t = Transaction.objects.create(
                active=True,
                content_type=ContentType.objects.get_for_model(Participation),
                object_id=participation.id,
                amount=value,
                customer=customer,
                method=method)
        elif ticket:
            ticket = Ticket.objects.get_unused_tickets(participation.participant.rider, participation.start).filter(type=ticket).order_by('expires')[0]
            ticket.transaction = transactions.filter(amount__lt=0)[0]
            ticket.save()

from django.utils import timezone
class ParticipationTransactionActivator(TransactionActivator):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return unicode(self.participation) + ': ' + unicode(self.fee)
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
        if self.participation.state == ATTENDING:
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
    if parti.state == ATTENDING:
        # If there is deactivated stuff
        trans = trans.filter(active=False)
        course = parti.event.course #Course.objects.filter(events__in=[parti.event])
        metadata = EventMetaData.objects.filter(event=parti.event, start=parti.start, end=parti.end)
        if course:
            #course = course[0]
            if trans:
              for t in trans:
                t.active=True
                t.save()
                if not Ticket.objects.filter(transaction=t).exists() and t.amount < 0:
                  tickets = parti.participant.rider.unused_tickets.filter(type__in=course.ticket_type.all())
                  _use_ticket(tickets, t)
            else:
              ParticipationTransactionActivator.objects.try_create(parti, course.default_participation_fee, course.ticket_type.all())
        elif metadata:
            metadata = metadata[0]
            ParticipationTransactionActivator.objects.try_create(parti, metadata.default_participation_fee)
    elif parti.state == CANCELED or parti.state == RESERVED:
        ParticipationTransactionActivator.objects.filter(participation=parti).delete()
        trans.deactivate()
        for ticket in Ticket.objects.filter(transaction__in=trans):
          ticket.transaction = None
          ticket.save()


def _get_actual_state(self):
    if self.state == WAITFORPAY:
        type = ContentType.objects.get_for_model(self)
        sum = Transaction.objects.filter(object_id=self.id, content_type=type).aggregate(Sum('amount'))['amount__sum']
        if sum >= 0:
            return ATTENDING
    return self.state
Enroll.actual_state = property(_get_actual_state)

