from decimal import Decimal
from tastypie.bundle import Bundle
from stables.models.common import TicketType
from stables.models.participations import Participation
from tastypie import fields
from stables.backbone import ParticipationPermissionAuthentication
from tastypie.resources import Resource
from stables.models import ATTENDING, SKIPPED
from stables.models.financial import Ticket, pay_participation
from django.utils.translation import ugettext as _
from stables.utils import getPaymentLink
from django.conf import settings

__author__ = 'jorutila'

class ViewFinance:
    def __init__(self, part=None):
        self.id = 0
        if part:
            self.id = part.id
            saldo, ticket, value, payment_method = part.get_saldo()
            if value:
                value = value.quantize(Decimal('0.01'))
            self.tickets = {}
            self.method = ""

            unused = Ticket.objects.get_unused_tickets(part.participant.rider, part.start)
            #unused = part.participant.rider.unused_tickets
            for u in unused:
                if (not ticket) or (ticket.type != u.type):
                    self.tickets[u.type.id] = u.type.name
            self.participation_url = part.get_absolute_url()
            self.finance_hint = unicode(value)
            if saldo and saldo < Decimal('0.00'):
                self.finance_hint = unicode(saldo)
            else:
                try:
                    method = part.get_pay_transaction().method or _('Cash')
                    method = method.title()
                except IndexError:
                    method = _('Cash')
                self.finance_hint = method + " " + unicode(value)

            if ticket:
                if value:
                    self.amount = value
                self.method = ticket.type.id
                self.finance_hint = unicode(ticket)
            else:
                if value == None or saldo < Decimal('0.00'):
                    self.amount = value

            if part.state != ATTENDING and part.state != SKIPPED:
                self.tickets = {}
                from stables.models import PARTICIPATION_STATES
                self.finance_hint = PARTICIPATION_STATES[part.state][1]

            self.linkmethods = []
            if part.participant.phone_number:
                self.linkmethods.append('mobile')
            if part.participant.user.email:
                self.linkmethods.append('email')

class FinanceResource(Resource):
    class Meta:
        resource_name = "financials"
        always_return_data = True
        object_class = ViewFinance
        authentication = ParticipationPermissionAuthentication()

    id = fields.IntegerField(attribute='id')
    finance_hint = fields.CharField(attribute='finance_hint', null=True)
    participation_url = fields.CharField(attribute='participation_url')

    amount = fields.CharField(attribute='amount', null=True)
    method = fields.CharField(attribute='method')

    tickets = fields.DictField(attribute='tickets', null=True)
    linkmethods = fields.ListField(attribute='linkmethods')

    def obj_get(self, bundle, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        return ViewFinance(part)

    def obj_update(self, bundle, request=None, **kwargs):
        part = Participation.objects.get(pk=kwargs['pk'])
        amount = bundle.data['amount']
        method = bundle.data['method']
        try:
            pay_participation(part, ticket=TicketType.objects.get(pk=int(method)))
        except ValueError:
            pay_participation(part, value = Decimal(amount) if amount != "" else None, method=method.lower())
        bundle.obj = ViewFinance(part)
        return bundle

class PaymentLinkObject():
    pass

class PaymentLinkResource(Resource):
    participation_id = fields.IntegerField(attribute="participation_id")
    method = fields.CharField(attribute="method")
    url = fields.CharField(attribute="url")
    extra = fields.CharField(attribute="extra", null=True)

    class Meta:
        resource_name = 'paymentlink'
        authentication = ParticipationPermissionAuthentication()
        object_class = PaymentLinkObject
        always_return_data = True

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.participation_id
        else:
            kwargs['pk'] = bundle_or_obj.participation_id
        return kwargs

    def obj_create(self, bundle, **kwargs):
        bundle.obj = PaymentLinkObject()
        bundle.obj.method = bundle.data['method']
        bundle.obj.participation_id = bundle.data['participation_id']
        shortUrl = getPaymentLink(bundle.obj.participation_id)
        url = bundle.request.build_absolute_uri(shortUrl)
        bundle.obj.url = url
        #TODO: Change to use settings implementations!
        part = Participation.objects.get(pk=bundle.obj.participation_id)
        if (bundle.obj.method == 'email'):
            message = 'Go pay your participation %s at url: %s' % (part, url)
            from django.core.mail import send_mail
            if ('extra' in bundle.data):
                part.participant.user.email = bundle.data['extra']
                part.participant.user.save()
            addr = part.participant.user.email
            if addr:
                send_mail('Subject', message, 'noreply@stables.fi', [addr])
        elif (bundle.obj.method == "mobile"):
            import django_settings
            message = u'Go pay your participation %s using (%s)' % (part, url) #django_settings.get('part_pay_info'))
            from django_twilio.client import twilio_client
            if ('extra' in bundle.data):
                part.participant.phone_number = bundle.data['extra']
                part.participant.save()
            nmbr = part.participant.phone_number
            msg = twilio_client.messages.create(
                body=message,
                to=settings.TEST_SMS or nmbr,
                from_='+358 45 73963377'
            )
            bundle.obj.extra = msg.sid
        return bundle

