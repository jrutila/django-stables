from django.db import models
from user import CustomerInfo, RiderInfo
import datetime
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db.models.signals import post_save
from django.dispatch import receiver

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

class Ticket(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        s = self.type.__unicode__() + ' (' + self.rider.__unicode__() + ')'
        if self.transaction:
            s = s + "(USED)"
        return s
    type = models.ForeignKey(TicketType)
    rider = models.ForeignKey(RiderInfo)
    transaction = models.ForeignKey("Transaction", null=True, blank=True)
    expires = models.DateTimeField(default=datetime.datetime.now()+datetime.timedelta(days=356), null=True, blank=True)

class TransactionActivator(models.Model):
    class Meta:
        app_label = 'stables'
        abstract = True

from participations import Course, Participation
import participations
class ParticipationTransactionActivatorManager(models.Manager):
    def try_create(self, participation, fee, ticket_type=None):
        if self.filter(participation=participation).count() > 0:
            return
        part_type = ContentType.objects.get_for_model(participation)
        if Transaction.objects.filter(content_type__pk=part_type.id, object_id=participation.id).count() > 0:
            return
        # TODO: 2400 to something right
        act = self.create(participation=participation, fee=fee, activate_before_hours=2400)
        act.ticket_type = ticket_type
        return act

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
        t = None
        if self.participation.start-datetime.timedelta(hours=self.activate_before_hours) < datetime.datetime.now():
            if self.participation.state == participations.ATTENDING:
                t = Transaction()
                t.amount = self.fee*-1
                t.customer = self.participation.participant.rider.customer
                t.source = self.participation
                t.save()
                tickets = self.participation.participant.rider.unused_tickets
                tickets = tickets.filter(type__in=self.ticket_type.all())
                if tickets.count() > 0:
                    ticket = tickets.order_by('expires')[0]
                    ticket.transaction = t
                    ticket.save()
            self.delete()
        return t


@receiver(post_save, sender=Participation)
def handle_Participation_save(sender, **kwargs):
    parti = kwargs['instance']
    # Only if the user is attending
    if parti.state == participations.ATTENDING:
        course = Course.objects.filter(events__in=[parti.event])[0]
        ParticipationTransactionActivator.objects.try_create(parti, course.default_participation_fee, course.ticket_type.all())

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

class Transaction(models.Model):
    class Meta:
        app_label = 'stables'
        permissions = (
            ('can_view_saldo', "Can see transactions and saldo"),
        )
    def __unicode__(self):
        #if self.source:
            #name = self.source.__unicode__() 
        name = self.customer.__unicode__() + ': ' + str(self.amount)
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

class TicketForm(forms.ModelForm):
  class Meta:
    model = Ticket
    exclude = ['transaction']

  amount = forms.IntegerField(required=True, initial=10)

  def save_all(self):
    amnt = self.cleaned_data['amount']
    for i in range(0, amnt):
      super(TicketForm, self).save(commit=True)
      self.instance.id = None
