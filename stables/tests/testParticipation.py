from stables.models import Participation
from stables.models import UserProfile
from stables.models import CustomerInfo, RiderInfo
from django.contrib.auth.models import User
from nose.tools import * #assert_equals, assert_is_not_none
from helpers import *
from testCourse import CourseTestBase
import reversion

attrs = [ 'start', 'end', 'event', 'state' ]
def pToList(parts):
    ret = []
    for p in parts:
        r = {}
        for a in attrs:
            if hasattr(p, a) and getattr(p, a):
                if a == 'event':
                    r[a] = list(p.event.course_set.all()[0].events.all()).index(p.event)
                else:
                    r[a] = getattr(p, a)
        ret.append(r)
    return ret

class CourseParticipationTest(CourseTestBase):
    @classmethod
    def setUpClass(cls):
        user = User.objects.get_or_create(username='test', first_name='test', last_name='user')[0]
        cls.rider = UserProfile.objects.get_or_create(user=user)[0]
        cls.rider.customer = CustomerInfo.objects.create()
        cls.rider.rider = RiderInfo.objects.create(customer=cls.rider.customer)
        cls.rider.save()

    def parts(self, parts):
        Participation.objects.all().delete()
        self.ps = []
        for p in parts:
            p['participant'] = self.rider
            if 'event' in p:
                p['event'] = self.course.events.all()[p['event']]
            if not 'start' in p:
                p['start'] = p['event'].start
            if not 'end' in p:
                p['end'] = p['event'].end
            px = Participation(**p)
            px.save()
            self.ps.append(px)

    def event(self, ind):
        return self.course.events.all()[ind]

    def check(self, parts):
        self.ps = list(Participation.objects.all())
        ps = pToList(self.ps)
        assert_equals.im_class.maxDiff = None
        assert_equals(ps, parts)

    def testParticipationChangesWhenEventChanges(self):
        self.events(
                [ { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    } ]
                )

        self.parts(
                [
                    { 'event': 0
                        },
                ]
                )

        occ = self.event(0).get_occurrences(self.event(0).start, self.event(0).end)[0]
        occ.move(dt('2014-01-02 12:30'), dt('2014-01-02 13:30'))

        self.check(
                [
                    { 'event': 0
                     ,'start': occ.start
                     ,'end': occ.end
                        },
                ]
                )

    def testParticipationCancelsWhenEventCancels(self):
        self.events(
                [ { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    } ]
                )

        self.parts(
                [
                    { 'event': 0
                     ,'state': 0
                        },
                ]
                )

        occ = self.event(0).get_occurrences(self.event(0).start, self.event(0).end)[0]
        occ.cancel()

        self.check(
                [
                    { 'event': 0
                     ,'start': occ.start
                     ,'end': occ.end
                     ,'state': 3
                        },
                ]
                )

    def testOtherParticipationDoesNotChangeWhenEventChanges(self):
        self.events(
                [
                    { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    },
                    { 'start': dt('2014-01-02 14:00'),
                    'end': dt('2014-01-02 14:30'),
                    },
                    ]
                )

        self.parts(
                [
                    { 'event': 0
                        },
                    { 'event': 1
                        },
                ]
                )

        occ = self.event(1).get_occurrences(self.event(1).start, self.event(1).end)[0]
        occ.move(dt('2014-01-02 15:00'), dt('2014-01-02 15:30'))

        self.check(
                [
                    { 'event': 0
                     ,'start': dt('2014-01-02 12:00')
                     ,'end': dt('2014-01-02 12:30')
                        },
                    { 'event': 1
                     ,'start': dt('2014-01-02 15:00')
                     ,'end': dt('2014-01-02 15:30')
                        },
                ]
                )

    def testParticipationChangeWhenCourseChanges(self):
        self.events(
                [
                    { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    },
                    { 'start': dt('2014-01-02 14:00'),
                      'end': dt('2014-01-02 14:30'),
                      'rule': 'w'
                    },
                    ]
                )

        self.parts(
                [
                    { 'event': 0
                        },
                    { 'event': 1
                     ,'start': dt('2014-01-02 14:00')
                     ,'end': dt('2014-01-02 14:30')
                        },
                    { 'event': 1
                     ,'start': dt('2014-01-09 14:00')
                     ,'end': dt('2014-01-09 14:30')
                        },
                ]
                )

        with reversion.create_revision():
          self.course.save(
                starttime=t('15:00'),
                endtime=t('15:30'),
                since=dt('2014-01-03 00:00'))

        self.check(
                [
                    { 'event': 0
                     ,'start': dt('2014-01-02 12:00')
                     ,'end': dt('2014-01-02 12:30')
                        },
                    { 'event': 1
                     ,'start': dt('2014-01-02 14:00')
                     ,'end': dt('2014-01-02 14:30')
                        },
                    { 'event': 2
                     ,'start': dt('2014-01-09 15:00')
                     ,'end': dt('2014-01-09 15:30')
                        },
                ]
                )
