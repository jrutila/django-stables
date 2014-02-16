from django.utils import unittest
from stables.models import Course
from schedule.models import Event
from schedule.models import Rule
from datetime import datetime
from nose.tools import * #assert_equals, assert_is_not_none
from . import *
import reversion

attrs = [ 'start', 'end', 'title', 'end_recurring_period', 'rule', 'name' ]
def evToList(events):
    ret = []
    for e in events:
        r = {}
        for a in attrs:
            if hasattr(e, a) and getattr(e, a):
                r[a] = getattr(e, a)
                if isinstance(r[a], Rule):
                    r[a] = str(r[a].name[0].lower())
                if a == 'title':
                    r[a] = str(r[a])
        ret.append(r)
    return ret
    

class CourseTestBase(unittest.TestCase):
    def setUp(self):
        self.course = None

    def events(self, events):
        self.course = Course()
        if events:
            ev = None
            for e in events:
                if 'rule' in e:
                    e['rule'] = Rule.objects.get(name="Weekly")
                ev = Event(**e)
                if 'end_recurring_period' in e:
                    ev.rule = Rule.objects.get(name="Weekly")
                ev.save()
                if not self.course.start:
                    self.course.start = ev.start.date()
                    self.course.save()
                self.course.events.add(ev)
            self.course.name = ev.title
            self.course.save()

    def check(self, events):
        ev = evToList(self.course.events.all())
        assert_equals.im_class.maxDiff = None
        assert_equals(ev, events)

class CourseTest(CourseTestBase):
    def testNewCourse(self):
        self.events(
                []
                )

        self.course.start = d('2014-01-02')

        self.course.save(starttime=t('12:00'), endtime=t('12:30'))

        self.check(
                [ { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'rule': 'w'} ]
                )

    def testNewCourseWithEnd(self):
        self.events(
                []
                )

        self.course.start = d('2014-01-02')
        self.course.end = d('2014-01-09')

        self.course.save(starttime=t('12:00'), endtime=t('12:30'))

        self.check(
                [ { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'} ]
                )

    def testCourseMoveTime(self):
        self.events(
                [ { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'rule': 'w' } ]
                )

        self.course.save(
                starttime=t('12:30')
               ,endtime=t('13:30')
               ,since=dt('2014-01-14 12:00'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'}
                    ,
                  { 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'rule': 'w'}
                ]
            )

    def testCourseMoveTimeAfterSecondSet(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'}
                    ,
                  { 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'rule': 'w'}
                ]
                )

        self.course.save(
                starttime=t('13:00')
               ,endtime=t('13:30')
               ,since=dt('2014-01-26 12:00'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'end_recurring_period': dt('2014-01-23 13:30'),
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-30 13:00'),
                    'end': dt('2014-01-30 13:30'),
                    'rule': 'w'}
                ]
            )

    def testCourseMoveTimeAndEnd(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'}
                    ,
                  { 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'rule': 'w'}
                ]
                )

        self.course.end = d('2014-02-06')
        self.course.save(
                      starttime=t('13:00')
                     ,endtime=t('13:30')
                     ,since=dt('2014-01-24 12:00'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'end_recurring_period': dt('2014-01-23 13:30'),
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-30 13:00'),
                    'end': dt('2014-01-30 13:30'),
                    'end_recurring_period': dt('2014-02-06 13:30'),
                    'rule': 'w'}
                ]
            )

    def testCourseEnd(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'}
                    ,
                  { 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'rule': 'w'}
                ]
                )

        self.course.end = d('2014-02-06')
        self.course.save(
                starttime=t('12:30')
               ,endtime=t('13:30')
               ,since=dt('2014-01-29 12:00'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'end_recurring_period': dt('2014-02-06 13:30'),
                    'rule': 'w'}
                ]
            )

    def testCourseName(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                ]
                )

        self.course.name='B'
        self.course.save(
               since=dt('2014-01-29 12:00'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-23 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-30 12:00'),
                    'end': dt('2014-01-30 12:30'),
                    'title': 'B',
                    'rule': 'w'}
                ]
            )

    def testCourseNameAndStarttime(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                    ,
                  { 'start': dt('2014-01-16 12:00'),
                    'end': dt('2014-01-16 12:30'),
                    'title': 'B',
                    'rule': 'w'}
                ]
                )

        self.course.name = 'C'
        self.course.save(
                starttime=t('12:30')
               ,endtime=t('13:30')
               ,since=dt('2014-01-23 12:30'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-16 12:00'),
                    'end': dt('2014-01-16 12:30'),
                    'end_recurring_period': dt('2014-01-23 12:30'),
                    'title': 'B',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-30 12:30'),
                    'end': dt('2014-01-30 13:30'),
                    'title': 'C',
                    'rule': 'w'}
                ]
            )

    def testCourseChangeNameFutureEvent(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-30 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-02-06 12:00'),
                    'end': dt('2014-02-06 12:30'),
                    'title': 'B',
                    'rule': 'w'}
                ]
                )

        self.course.name = 'X'
        self.course.save(
                starttime=t('12:00')
               ,endtime=t('12:30')
               ,since=dt('2014-02-05 12:30'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-30 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-02-06 12:00'),
                    'end': dt('2014-02-06 12:30'),
                    'title': 'X',
                    'rule': 'w'}
                ]
            )

    def testCourseChangeTimeFutureEvent(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-30 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-02-06 12:00'),
                    'end': dt('2014-02-06 12:30'),
                    'title': 'B',
                    'rule': 'w'}
                ]
                )

        self.course.save(
                starttime=t('12:30')
               ,endtime=t('13:30')
               ,since=dt('2014-02-06 12:00'))

        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-30 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-02-06 12:30'),
                    'end': dt('2014-02-06 13:30'),
                    'title': 'B',
                    'rule': 'w'}
                ]
            )

    def testCourseChangeTimeMiddleEvent(self):
        self.events(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'end_recurring_period': dt('2014-01-30 12:30'),
                    'title': 'B',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-02-06 14:00'),
                    'end': dt('2014-02-06 14:30'),
                    'title': 'C',
                    'rule': 'w'}
                ]
                )

        self.course.save(
                starttime=t('13:30')
               ,endtime=t('14:00')
               ,since=dt('2014-01-18 12:00'))

        # This should be prevented for example in the form
        # but this is what happens with this combination
        self.check(
                [
                  { 'start': dt('2014-01-02 12:00'),
                    'end': dt('2014-01-02 12:30'),
                    'end_recurring_period': dt('2014-01-09 12:30'),
                    'title': 'A',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-01-16 12:30'),
                    'end': dt('2014-01-16 13:30'),
                    'end_recurring_period': dt('2014-01-30 12:30'),
                    'title': 'B',
                    'rule': 'w'}
                 ,{ 'start': dt('2014-02-06 13:30'),
                    'end': dt('2014-02-06 14:00'),
                    'title': 'C',
                    'rule': 'w'}
                ]
                )

    def testCourseChangeTimeFutureOccurrenceChangePrevails(self):
        #TODO
        pass
