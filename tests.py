from django.utils import unittest
from stables.models import Participation
from stables.models import ParticipationTransactionActivator
from stables.models import Ticket, TicketType
from django.auth import User

class TicketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        user = User.objects.get_or_create(username='user')
        type = TicketType.objects.get_or_create(name='testtype')
        user.rider = RiderInfo()
        user.rider.save()
        user.customer = CustomerInfo()
        user.customer.save()
        user.rider.customer = user.customer
        user.rider.save()
        cls.user = user
        cls.ticket_type = type

    def testUnusedTickets(self):
        rider = user.get_profile().rider
        t1 = Ticket.objects.create(type=self.ticket_type, rider=rider, expires=datetime.datetime.now()+datetime.timedelta(days=10))
        t2 = Ticket.objects.create(type=self.ticket_type, rider=rider, expires=datetime.datetime.now()+datetime.timedelta(days=5))
        t3 = Ticket.objects.create(type=self.ticket_type, rider=rider, expires=None)

        tickets = rider.unused_tickets
        self.assertEqual(tickets.count(), 3)
        self.assertEqual(tickets[0].id, t2.id)
        t2.expires = datetime.datetime.now()-datetime.timedelta(hours=1)
        t2.save()
        self.assertEqual(tickets.count(), 2)
        trans = Transaction.objects.create(customer=user.get_profile().customer, amount=25)
        t1.transaction = trans
        t1.save()
        self.assertEqual(tickets.count(), 1)

class ActivatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from schedule.models import Calendar, Rule, Event
        from django.contrib.auth.models import User
        cal = Calendar()
        cal.save()
        rule = Rule(frequency = "WEEKLY", name = "Weekly")
        rule.save()
        event = Event(calendar=cal,rule=rule, start=datetime.datetime.now()+datetime.timedelta(hours=10), end=datetime.datetime.now()+datetime.timedelta(hours=12))
        event.save()
        user = User(username='user',first_name='Test', last_name='Guy')
        user.save()
        prof = user.get_profile()
        customer = CustomerInfo()
        customer.address = 'Address'
        customer.save()
        rider = RiderInfo()
        rider.customer = customer
        rider.save()
        prof.rider = rider
        prof.save()

        cls.user = user
        cls.event = event

    def testActivation(self):
        user = self.user
        event = self.event
        Participation.objects.all().delete()
        p1 = Participation()
        p1.state=1
        p1.event=event
        p1.start=event.start
        p1.end=event.end
        p1.participant = user.get_profile()
        p1.save()
        pa = ParticipationTransactionActivator()
        pa.participation = p1
        pa.activate_before_hours = 15
        pa.fee = 45.15
        pa.save()
        t = pa.try_activate()
        self.assertEqual(t.amount, pa.fee*-1)
        count = ParticipationTransactionActivator.objects.count()
        self.assertEqual(count, 0)
        self.assertEqual(t.customer, p1.participant.rider.customer)
        self.assertTrue(t.active)
        self.assertEqual(t.source, p1)

    def testActivateOnlyAttending(self):
        from stables import models as stblenum
        user = self.user
        event = self.event
        Participation.objects.all().delete()
        p1 = Participation()
        p1.state=stblenum.CANCELED
        p1.event=event
        p1.start=event.start
        p1.end=event.end
        p1.participant = user.get_profile()
        p1.save()
        pa = ParticipationTransactionActivator()
        pa.participation = p1
        pa.activate_before_hours = 15
        pa.fee = 45.15
        pa.save()
        t = pa.try_activate()
        self.assertIsNone(t)
        count = ParticipationTransactionActivator.objects.count()
        self.assertEqual(count, 0)

