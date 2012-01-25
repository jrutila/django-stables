from django.utils import unittest
from stables.models import Participation, Enroll
from stables.models import ParticipationTransactionActivator
from stables.models import CourseParticipationActivator
from stables.models import Ticket, TicketType, Transaction
from stables.models import RiderInfo, CustomerInfo
from stables.models import Course
from schedule.models import Calendar, Event, Rule
from django.contrib.auth.models import User
import datetime
from stables.models import ATTENDING, CANCELED, RESERVED
from decimal import *

def setupRider(name):
    user, created = User.objects.get_or_create(username=name)
    user.last_name = name
    user.save()
    customer = CustomerInfo.objects.create()
    profile = user.get_profile()
    rider = RiderInfo()
    rider.customer = customer
    rider.save()
    profile.rider = rider
    profile.customer = customer
    profile.save()

    return user

def setupCourse(name, start, end, starttime, endtime):
    cal, created = Calendar.objects.get_or_create(name="Main Calendar", slug="main")
    rule, created = Rule.objects.get_or_create(name="Weekly", frequency="WEEKLY")
    course = Course()
    course.name='course1'
    course.start=start
    course.end=end
    course.save()
    event = Event(calendar=cal, rule=rule, start=datetime.datetime.combine(course.start, starttime), end=datetime.datetime.combine(start, endtime))
    if end:
      event.end_recurring_period=datetime.datetime.combine(end, endtime)
    event.save()
    course.events.add(event)
    course.save()
    return course

class CourseOccurrenceTest(unittest.TestCase):
    def testCourseOccurrences(self):
        # Four weeks course
        start=datetime.date.today()
        end=datetime.date.today()+datetime.timedelta(days=21)
        starttime=datetime.time(11,00)
        endtime=datetime.time(12,00)
        course = setupCourse('course1', start, end, starttime, endtime)

        occs = course.get_occurrences()
        self.assertEqual(len(occs), 4)

    def testCourseOccurrencesWithoutEnd(self):
        start=datetime.date.today()
        starttime=datetime.time(11,00)
        endtime=datetime.time(12,00)
        course = setupCourse('course1', start, None, starttime, endtime)

        occs = course.get_occurrences()
        self.assertEqual(len(occs), 52)

    def testCourseOccurrencesWithDelta(self):
        start=datetime.date.today()
        end=datetime.date.today()+datetime.timedelta(days=21)
        starttime=datetime.time(11,00)
        endtime=datetime.time(12,00)
        course = setupCourse('course1', start, end, starttime, endtime)

        occs = course.get_occurrences(delta=datetime.timedelta(days=14))
        self.assertEqual(len(occs), 3)

class TicketTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = setupRider('user')
        type, created = TicketType.objects.get_or_create(name='testtype')
        cls.ticket_type = type

    def testUnusedTickets(self):
        rider = self.user.get_profile().rider
        t1 = Ticket.objects.create(type=self.ticket_type, rider=rider, expires=datetime.datetime.now()+datetime.timedelta(days=10))
        t2 = Ticket.objects.create(type=self.ticket_type, rider=rider, expires=datetime.datetime.now()+datetime.timedelta(days=5))
        t3 = Ticket.objects.create(type=self.ticket_type, rider=rider, expires=None)

        tickets = rider.unused_tickets
        self.assertEqual(tickets.count(), 3)
        self.assertEqual(tickets[0].id, t1.id)
        t2.expires = datetime.datetime.now()-datetime.timedelta(hours=1)
        t2.save()
        self.assertEqual(tickets.count(), 2)
        trans = Transaction.objects.create(customer=self.user.get_profile().customer, amount=25)
        t1.transaction = trans
        t1.save()
        self.assertEqual(tickets.count(), 1)

class ActivatorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        prof.customer = customer
        prof.save()

        cls.user = user
        cls.event = event

    def testCourseParticipationActivator(self):
        user = self.user
        now = datetime.datetime.now()
        ss = now+datetime.timedelta(hours=5)
        ee = now+datetime.timedelta(hours=6)
        starttime = ss.time()
        endtime = ee.time()
        start = ss.date()-datetime.timedelta(days=7)
        course = setupCourse('course1', start, None, starttime, endtime)
        enroll = Enroll.objects.create(course=course, participant=user.get_profile(), state=RESERVED)
        pa = CourseParticipationActivator.objects.filter(enroll=enroll)

        # No CETA yet
        self.assertEqual(pa.count(), 0)

        enroll.state = ATTENDING
        enroll.save()

        # Should create a new CETA
        self.assertEqual(pa.count(), 1)

        self.assertEqual(pa[0].enroll, enroll)

    def testCourseParticipationActivation(self):
        user = self.user
        now = datetime.datetime.now()
        ss = now+datetime.timedelta(hours=5)
        ee = now+datetime.timedelta(hours=6)
        starttime = ss.time()
        endtime = ee.time()
        start = ss.date()-datetime.timedelta(days=7)
        course = setupCourse('course1', start, None, starttime, endtime)
        enroll = Enroll.objects.create(course=course, participant=user.get_profile(), state=ATTENDING)
        ca = CourseParticipationActivator.objects.filter(enroll=enroll)[0]
        pa = Participation.objects.filter(event=course.events.all()[0])

        self.assertEqual(pa.count(), 0)

        ca.try_activate()

        self.assertEqual(pa.count(), 1)

    def testParticipationTransactionCreation(self):
        user = self.user
        now = datetime.datetime.now()
        ss = now+datetime.timedelta(hours=5)
        ee = now+datetime.timedelta(hours=6)
        starttime = ss.time()
        endtime = ee.time()
        start = ss.date()-datetime.timedelta(days=7)
        course = setupCourse('course1', start, None, starttime, endtime)
        course.default_participation_fee=45.16
        course.save()
        o = course.get_occurrences()[1]
        pa = ParticipationTransactionActivator.objects.filter()

        self.assertEqual(pa.count(), 0)

        p = course.create_participation(user.get_profile(), o, ATTENDING, True)

        self.assertEqual(pa.count(), 1)
        self.assertEqual(pa[0].fee, Decimal('45.16'))

    def testParticipationTransactionActivation(self):
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

from stables.models import CourseForm
class CourseEnrollTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        user = setupRider('user')
        data = { 'start': datetime.datetime.today()-datetime.timedelta(days=14),
                 'end': datetime.datetime.today()+datetime.timedelta(days=14),
                 'max_participants': 2,
                 'name': 'Test course',
                 'creator': 0,
                 'course_fee': 1200,
                 'default_participation_fee': 0,
                 'creator': user.id,
                 'created_on': datetime.datetime.now(),
                 'starttime': datetime.time(13, 00),
                 'endtime': datetime.time(15, 00),
               }
        course = CourseForm(data)
        cls.course=course.save()
        cls.user = user

    def setUp(self):
        self.course.max_participants=2
        self.course.save()
        Enroll.objects.all().delete()
        Participation.objects.all().delete()

    def runStates(self, table):
        (users) = self.runHelper(table)
        for (i, u) in enumerate(users):
            result = self.course.get_possible_states(u)
            self.assertEqual(set(result), set(table[i][1]), "user%d: " % i + str(result) )

    def runHelper(self, table):
        users = []
        for (i, row) in enumerate(table):
            us = setupRider('user'+str(i)).get_profile()
            users.append(us)
            row.append(us)
        if len(table[0]) > 4:
            table = sorted(table, key=lambda x: x[3][0])
        for (i, row) in enumerate(table):
            if row[0] is not None:
                Enroll.objects.create(course=self.course, participant=row[-1], state=row[0])
        return (users)

    def testCourseEnroll(self):
        course = self.course
        user = self.user.get_profile()

        course.enroll(user)

        e = Enroll.objects.all()[0]
        self.assertEqual(e.participant, user)
        self.assertEqual(e.state, ATTENDING)

    def testCourseEnroll(self):
        course = self.course
        user = self.user.get_profile()

        course.enroll(user)

        e = Enroll.objects.all()[0]
        ex = course.enroll(user)

        self.assertEqual(Enroll.objects.count(), 1)
        self.assertEqual(ex, e)
        self.assertEqual(e.participant, user)
        self.assertEqual(e.state, ATTENDING)

    def testCourseEnrollWhenFull(self):
        course = self.course
        user = self.user.get_profile()
        user2 = setupRider('user2').get_profile()
        user3 = setupRider('user3').get_profile()

        course.enroll(user)
        course.enroll(user2)
        # Now it is full
        ex = course.enroll(user3)

        self.assertEqual(Enroll.objects.count(), 3)
        e = Enroll.objects.all()[2]
        self.assertEqual(ex, e)
        self.assertEqual(e.participant, user3)
        self.assertEqual(e.state, RESERVED)

    def testCourseDoubleEnrollWhenFull(self):
        course = self.course
        user = self.user.get_profile()
        user2 = setupRider('user2').get_profile()
        user3 = setupRider('user3').get_profile()

        course.enroll(user)
        course.enroll(user2)
        # Now it is full, Enroll user again
        ex = course.enroll(user)

        self.assertEqual(Enroll.objects.count(), 2)
        e = Enroll.objects.all()[0]
        self.assertEqual(ex, e)
        self.assertEqual(e.participant, user)
        self.assertEqual(e.state, ATTENDING)
        

    def testPossibleStateWhenEmpty(self):
        states = self.course.get_possible_states(self.user)
        self.assertEqual(len(states), 1)
        self.assertEqual(states[0], ATTENDING)

    def testPossibleStatesWhenEmpty(self):
        #        enroll    , allowed
        data = [
                [ None     , [ATTENDING] ],
                [ None     , [ATTENDING] ],
               ]
        self.runStates(data)
        
    def testPossibleStatesWhenPartialEmpty(self):
        #        enroll    , allowed
        data = [
                [ ATTENDING, [CANCELED ] ],
                [ None     , [ATTENDING] ],
               ]
        self.runStates(data)

    def testPossibleStatesWhenFull(self):
        #        enroll    , allowed
        data = [
                [ ATTENDING, [CANCELED ] ],
                [ CANCELED , [RESERVED ] ],
                [ CANCELED , [RESERVED ] ],
                [ ATTENDING, [CANCELED ] ],
                [ None     , [RESERVED ] ],
               ]
        self.runStates(data)

    def testPossibleStatesWhenFullAndReserved(self):
        #        enroll    , allowed
        data = [
                [ ATTENDING, [CANCELED ] ],
                [ ATTENDING, [CANCELED ] ],
                [ RESERVED , [CANCELED ] ],
                [ None     , [RESERVED ] ],
               ]
        self.runStates(data)

    def testPossibleStatesWhenInQueue(self):
        #        enroll    , allowed
        data = [
                [ ATTENDING, [CANCELED ] ],
                [ CANCELED , [RESERVED ] ],
                [ RESERVED , [ATTENDING, CANCELED ] ],
                [ RESERVED , [CANCELED ] ],
                [ None     , [RESERVED ] ],
                [ RESERVED , [CANCELED ] ],
               ]
        self.runStates(data)

class CourseParticipationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        user = setupRider('user')
        data = { 'start': datetime.datetime.today()-datetime.timedelta(days=14),
                 'end': datetime.datetime.today()+datetime.timedelta(days=14),
                 'max_participants': 2,
                 'name': 'Test course',
                 'creator': 0,
                 'course_fee': 1200,
                 'default_participation_fee': 0,
                 'creator': user.id,
                 'created_on': datetime.datetime.now(),
                 'starttime': datetime.time(13, 00),
                 'endtime': datetime.time(15, 00),
               }
        course = CourseForm(data)
        cls.course=course.save()
        cls.user = user

    def setUp(self):
        self.course.max_participants=2
        self.course.save()
        Enroll.objects.all().delete()
        Participation.objects.all().delete()

    def testStatesPast(self):
        # occ from past
        occ = self.course.get_occurrences()[0]
        states = self.course.get_possible_states(self.user, occ)
        self.assertEqual(len(states), 0)

    def runHelper(self, table):
        occ = self.course.get_occurrences()[-1]
        users = []
        for (i, row) in enumerate(table):
            us = setupRider('user'+str(i)).get_profile()
            users.append(us)
            row.append(us)
        if len(table[0]) > 4:
            table = sorted(table, key=lambda x: x[3][0])
        for (i, row) in enumerate(table):
            if row[0] is not None:
                Enroll.objects.create(course=self.course, participant=row[-1], state=row[0])
        if len(table[0]) > 4:
            table = sorted(table, key=lambda x: x[3][1])
        for (i, row) in enumerate(table):
            if row[1] is not None:
                self.course.create_participation(row[-1], occ, row[1], force=True)
        return (occ, users)

    def runFull(self, table, full):
        (occ, users) = self.runHelper(table)
        self.assertEqual(self.course.is_full(occ), full)

    def runFullRider(self, table):
        (occ, users) = self.runHelper(table)
        self.assertEqual(self.course.full_rider(occ), list(x[-1] for x in sorted(filter(lambda y: y[2] is not None, table), key=lambda x: x[2])))

    def runStates(self, table):
        (occ, users) = self.runHelper(table)
        for (i, u) in enumerate(users):
            result = self.course.get_possible_states(u, occ)
            self.assertEqual(set(result), set(table[i][2]), "user%d: " % i + str(result) )

    def testStatesEmpty(self):
        #        enroll    , part     , allowed
        data = [
                [ None     , None     , [ATTENDING] ],
                [ None     , None     , [ATTENDING] ],
               ]

        self.runStates(data)

    def testStatesEnroll(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, None     , [CANCELED] ],
                [ ATTENDING, None     , [CANCELED] ],
               ]

        self.runStates(data)

    def testStatesEnrollReservedAndNone(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, None     , [CANCELED] ],
                [ ATTENDING, None     , [CANCELED] ],
                [ RESERVED , None     , [CANCELED] ],
                [ None     , None     , [RESERVED] ],
               ]

        self.runStates(data)

    def testStatesEnrollReservedAndCanceled(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, None     , [CANCELED ] ],
                [ ATTENDING, CANCELED , [RESERVED ] ],
                [ RESERVED , None     , [ATTENDING, CANCELED] ],
                [ None     , None     , [RESERVED ] ],
               ]

        self.runStates(data)

    def testStates001(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ RESERVED , None     , [ATTENDING, CANCELED] ],
                [ None     , None     , [ATTENDING] ],
               ]

        self.runStates(data)

    def testStates001_1(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ RESERVED , ATTENDING, [CANCELED ] ],
                [ None     , None     , [ATTENDING] ],
               ]

        self.runStates(data)

    def testStates001_2(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, CANCELED , [RESERVED ] ],
                [ ATTENDING, CANCELED , [RESERVED ] ],
                [ RESERVED , None     , [ATTENDING, CANCELED ] ],
                [ None     , ATTENDING, [CANCELED ] ],
               ]

        self.runStates(data)

    def testStates002(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ RESERVED , CANCELED , [ATTENDING] ],
                [ None     , ATTENDING, [CANCELED ] ],
               ]

        self.runStates(data)

    def testStates003(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ ATTENDING, CANCELED , [ATTENDING] ],
                [ RESERVED , CANCELED , [ATTENDING] ],
                [ None     , RESERVED , [ATTENDING, CANCELED] ],
               ]

        self.runStates(data)

    def testStates004(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, CANCELED , [RESERVED ] ],
                [ ATTENDING, CANCELED , [RESERVED ] ],
                [ RESERVED , RESERVED , [ATTENDING, CANCELED] ],
                [ None     , RESERVED , [ATTENDING, CANCELED] ],
               ]

        self.runStates(data)

    def testStates005(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, None     , [CANCELED ] ],
                [ ATTENDING, None     , [CANCELED ] ],
                [ RESERVED , None     , [CANCELED ] ],
                [ CANCELED , None     , [RESERVED ] ],
               ]

        self.runStates(data)

    def testStates006(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, None     , [CANCELED ] ],
                [ ATTENDING, None     , [CANCELED ] ],
                [ RESERVED , RESERVED , [CANCELED ] ],
                [ None     , None     , [RESERVED ] ],
               ]

        self.runStates(data)

    def testFullRider001(self):
        #        enroll    , part     , fullorder  , order
        data = [
                [ ATTENDING, None     , 0          , [0, 0] ],
                [ None     , None     , None       , [1, 1] ],
                [ None     , None     , None       , [2, 2] ],
                [ None     , None     , None       , [3, 3] ],
               ]

        self.runFullRider(data)

    def testFullRider002(self):
        #        enroll    , part     , fullorder  , order
        data = [
                [ ATTENDING, None     , 0          , [0, 0] ],
                [ ATTENDING, CANCELED , None       , [1, 1] ],
                [ RESERVED , None     , 1          , [2, 2] ],
                [ None     , None     , None       , [3, 3] ],
               ]

        self.runFullRider(data)

    def testFullRider003(self):
        #        enroll    , part     , fullorder  , order
        data = [
                [ ATTENDING, None     , 0          , [0, 0] ],
                [ None     , RESERVED , None       , [1, 1] ],
                [ None     , ATTENDING, 1          , [2, 2] ],
                [ None     , None     , None       , [3, 3] ],
               ]

        self.runFullRider(data)

    def testFullRider004(self):
        #        enroll    , part     , fullorder  , order
        data = [
                [ ATTENDING, None     , 0          , [0, 0] ],
                [ RESERVED , None     , None       , [2, 1] ],
                [ RESERVED , None     , 1          , [1, 2] ],
                [ None     , None     , None       , [3, 3] ],
               ]

        self.runFullRider(data)

    def testFullRider005(self):
        #        enroll    , part     , fullorder  , order
        data = [
                [ ATTENDING, None     , 0          , [0, 0] ],
                [ RESERVED , None     , 1          , [2, 1] ],
                [ RESERVED , CANCELED , None       , [1, 2] ],
                [ None     , None     , None       , [3, 3] ],
               ]

        self.runFullRider(data)

    def testFullRider005(self):
        #        enroll    , part     , fullorder  , order
        data = [
                [ ATTENDING, CANCELED , None       , [0, 0] ],
                [ RESERVED , None     , None       , [2, 1] ],
                [ ATTENDING, None     , 0          , [1, 2] ],
                [ None     , ATTENDING, 1          , [3, 3] ],
               ]

        self.runFullRider(data)
    
    def testParticipationFull(self):
        #        enroll    , part     , allowed (not used)
        data = [
                [ None     , ATTENDING, [] ],
                [ None     , ATTENDING, [] ],
               ]
        self.runFull(data, True)

    def testEnrollFull(self):
        #        enroll    , part     , allowed (not used)
        data = [
                [ ATTENDING, None     , [] ],
                [ ATTENDING, None     , [] ],
               ]
        self.runFull(data, True)

    def testParticipationEnrollMixedFull(self):
        #        enroll    , part     , allowed (not used)
        data = [
                [ ATTENDING, None     , [] ],
                [ None     , ATTENDING, [] ],
               ]
        self.runFull(data, True)

    def testCourseCanceledFull(self):
        #        enroll    , part     , allowed (not used)
        data = [
                [ ATTENDING, None     , [] ],
                [ ATTENDING, CANCELED , [] ],
                [ None     , ATTENDING, [] ],
               ]
        self.runFull(data, True)

    def testReservedFull(self):
        #        enroll    , part     , allowed (not used)
        data = [
                [ None     , ATTENDING, [] ],
                [ None     , RESERVED , [] ],
               ]
        self.runFull(data, True)

    def testFull001(self):
        #        enroll    , part     , allowed
        data = [
                [ ATTENDING, None     , [CANCELED ] ],
                [ ATTENDING, CANCELED , [RESERVED ] ],
                [ RESERVED , None     , [ATTENDING] ],
                [ None     , None     , [RESERVED ] ],
               ]
        self.runFull(data, True)
