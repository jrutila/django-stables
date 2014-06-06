from django.utils import unittest
from stables.models import Participation
from stables.models import Ticket, TicketType
from stables.models import Transaction
from stables.models import UserProfile
from stables.models import CustomerInfo, RiderInfo
from stables.models import pay_participation
from schedule.models import Calendar
from schedule.models import Event
from django.contrib.auth.models import User
from nose.tools import * #assert_equals, assert_is_not_none
from helpers import *
import datetime
from decimal import Decimal

TWO = Decimal(10) ** -2

class FinanceTestBase(unittest.TestCase):
    _ticket = None

    @classmethod
    def setUpClass(cls):
        user = User.objects.create(first_name='test', last_name='user')
        customer = CustomerInfo.objects.create()
        cls.rider = UserProfile.objects.create(
                user=user,
                customer = customer,
                rider = RiderInfo.objects.create(customer=customer),
                )
        cls.rider.save()
        #cls.rider = user.get_profile()
        start=datetime.datetime(2014, 02, 04, 12, 0, 0)
        end=datetime.datetime(2014, 02, 04, 13, 0, 0)
        cal,c = Calendar.objects.get_or_create(slug='test')
        cls.event, c = Event.objects.get_or_create(calendar=cal, start=start, end=end)
        TicketType.objects.create(name="test")

    def setUp(self):
        self.part, c = Participation.objects.get_or_create(
                participant=self.rider,
                event=self.event,
                start=self.event.start,
                end=self.event.end
                )
        Ticket.objects.all().delete()
        Transaction.objects.all().delete()

    def trans(self, tr):
        for t in tr:
            trans = Transaction.objects.create(
                    amount=Decimal(t[0]),
                    source=self.part,
                    customer=self.rider.customer,
                    )
            if t[1]:
                t[1].transaction = trans
                t[1].save()
    def _createList(self, tr):
        ret = []
        for t in tr:
            ticket = None
            if t.ticket_set.count():
                ticket = t.ticket_set.all()[0]
            ret.append((str(t.amount.quantize(TWO)), ticket))
        return ret

    def check(self, tr):
        actual = self._createList(Transaction.objects.all())
        assert_equals(tr, actual)

    def unused(self, amnt):
        assert_equals(self.rider.rider.unused_tickets.count(), amnt)

    def saldo(self, *args):
        sld = self.part.get_saldo()
        assert_equals(args, (
            str(sld[0].quantize(TWO)) if sld[0] != None else None,
            sld[1],
            str(sld[2].quantize(TWO)) if sld[2] != None else None ))

    @property
    def ticket(self):
        if not self._ticket:
            self._ticket = Ticket()
            self._ticket.type = TicketType.objects.get(pk=1)
            self._ticket.owner = self.rider.rider
            self._ticket.save()
        return self._ticket


class PayParticipationTest(FinanceTestBase):
    def testNull(self):
        self.trans([])
        self.saldo(None, None, None)

    def testCashPayment(self):
        self.trans([
            ( '-35.00', None ),
                ])
        self.saldo('-35.00', None, '35.00')

        pay_participation(self.part)

        self.check([
            ( '-35.00', None ),
            ( '35.00', None ),
            ])

        self.saldo('0.00', None, '35.00')

    def testNullPayment(self):
        self.trans([
            ( '0.00', None ),
                ])
        self.saldo('0.00', None, '0.00')

        pay_participation(self.part)

        self.check([
            ( '0.00', None ),
            ])
        self.saldo('0.00', None, '0.00')

    def testNullifyPayment(self):
        self.trans([
            ( '-10.00', None ),
                ])
        self.saldo('-10.00', None, '10.00')

        pay_participation(self.part, value=Decimal('0.00'))

        self.check([
            ( '0.00', None ),
            ])
        self.saldo('0.00', None, '0.00')

    def testValueChange(self):
        self.trans([
            ( '-10.00', None ),
                ])
        self.saldo('-10.00', None, '10.00')

        pay_participation(self.part, value=Decimal('20.00'))

        self.check([
            ( '-20.00', None ),
            ( '20.00', None ),
            ])
        self.saldo('0.00', None, '20.00')

    def testTicketPayment(self):
        self.trans([
            ( '-15.00', None ),
                ])
        self.saldo('-15.00', None, '15.00')

        pay_participation(self.part, ticket=self.ticket.type)

        self.check([
            ( '-15.00', self.ticket ),
            ])
        self.saldo('0.00', self.ticket, '15.00')

    def testTicketPaymentAfterCash(self):
        self.trans([
            ( '-15.00', None ),
            ( '15.00', None ),
                ])
        self.saldo('0.00', None, '15.00')

        pay_participation(self.part, ticket=self.ticket.type)

        self.check([
            ( '-15.00', self.ticket ),
            ])
        self.saldo('0.00', self.ticket, '15.00')

    def testTicketNullify(self):
        self.trans([
            ( '-15.00', self.ticket ),
                ])
        self.saldo('0.00', self.ticket, '15.00')

        self.unused(0)
        pay_participation(self.part, value=Decimal('0.00'))

        self.check([
            ( '0.00', None ),
            ])
        self.unused(1)
        self.saldo('0.00', None, '0.00')

    def testTicketCash(self):
        self.trans([
            ( '-15.00', self.ticket ),
                ])
        self.saldo('0.00', self.ticket, '15.00')

        self.unused(0)
        pay_participation(self.part)

        self.check([
            ( '-15.00', None ),
            ( '15.00', None ),
            ])
        self.unused(1)
        self.saldo('0.00', None, '15.00')
