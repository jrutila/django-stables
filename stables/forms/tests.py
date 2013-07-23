from django.utils import unittest
from datetime import datetime, timedelta
from schedule.models import Event, Rule, Calendar
from stables.models import Course
from stables.models import Participation
from stables.models import UserProfile
from stables.forms import CourseForm
from django.contrib.auth.models import User
import sure


class CourseFormTest(unittest.TestCase):
    """
    Setup:
    Course 1 (start 2wk ago) 
        Event 1 (2wk-1wk) 17-18
        Event 2 (1wk-future)
    """
    def setUp(self):
        Course.objects.all().delete()
        Participation.objects.all().delete()
        cal, created = Calendar.objects.get_or_create(name="Main Calendar", slug="main")
        rule, created = Rule.objects.get_or_create(name="Weekly", frequency="WEEKLY")
        tomorrow = (datetime.now()+timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
        thrwkago = tomorrow-timedelta(days=21)
        twowkago = tomorrow-timedelta(days=14)
        onewkago = tomorrow-timedelta(days=7)

        start = thrwkago

        course = Course()
        course.name='Course 1'
        course.start=start
        course.end=None
        course.save()
        event = Event.objects.create(
                calendar=cal,
                rule=rule,
                start=thrwkago,
                end=thrwkago+timedelta(hours=1),
                end_recurring_period=twowkago+timedelta(hours=1)
                )
        course.events.add(event)
        event = Event.objects.create(
                calendar=cal,
                rule=rule,
                start=onewkago,
                end=onewkago+timedelta(hours=1),
                end_recurring_period=None
                )
        course.events.add(event)
        course.save()
        self.course1 = course

        self.user, created = User.objects.get_or_create(username='test')
        userprof, created = UserProfile.objects.get_or_create(user=self.user)

    def testBasicFormSave(self):
        start = (datetime.now()+timedelta(days=2)).replace(hour=17, minute=0, second=0, microsecond=0)
        data = {}
        data['name'] = 'Course 2'
        data['start'] = str(start.date())
        data['max_participants'] = 5
        data['starttime'] = '17:00'
        data['endtime'] = '18:00'
        data['default_participation_fee'] = '30.00'

        target = CourseForm(data=data)
        target.user = self.user

        target.is_valid().should.be.ok
        target.save()

        Course.objects.all().count().should.be.equal(2)
        course = Course.objects.get(pk=target.instance.id)
        course.events.count().should.be.equal(1)
        course.events.all()[0].start.should.be.equal(start)
        course.events.all()[0].end.should.be.equal(start+timedelta(hours=1))
        course.events.all()[0].rule.frequency.should.be.equal('WEEKLY')

    def testBasicFormUpdateStartTime(self):
        start = self.course1.events.all()[0].start+timedelta(hours=1)
        self.course1.events.count().should.be.equal(2)
        next_occ = self.course1.get_next_occurrence()

        data = {}
        data['name'] = 'Course 1'
        data['start'] = str(self.course1.start.date())
        data['max_participants'] = 5
        data['starttime'] = start.time().strftime('%H:%M')
        data['endtime'] = (start+timedelta(hours=1)).time().strftime('%H:%M')
        data['default_participation_fee'] = '30.00'
        data['take_into_account'] = datetime.now()

        target = CourseForm(instance=self.course1, data=data)
        target.user = self.user

        target.is_valid().should.be.ok
        target.save()

        Course.objects.all().count().should.be.equal(1)
        course = Course.objects.get(pk=target.instance.id)
        course.events.count().should.be.equal(3)
        event1 = course.events.all()[1]
        event1.end_recurring_period.should.be.equal(next_occ.end-timedelta(days=7))
        course.events.all()[2].start.should.be.equal(next_occ.start.replace(hour=start.hour))

    def testBasicFormEndCourse(self):
        start = self.course1.events.all()[1].start
        self.course1.events.count().should.be.equal(2)
        next_occ = self.course1.get_next_occurrence()

        data = {}
        data['name'] = 'Course 1'
        data['start'] = str(self.course1.start.date())
        data['max_participants'] = 5
        data['starttime'] = start.time().strftime('%H:%M')
        data['endtime'] = (start+timedelta(hours=1)).time().strftime('%H:%M')
        data['default_participation_fee'] = '30.00'
        data['take_into_account'] = datetime.now()

        data['end'] = str(next_occ.start.date())

        target = CourseForm(instance=self.course1, data=data)
        target.user = self.user

        target.is_valid().should.be.ok
        target.save()

        Course.objects.all().count().should.be.equal(1)
        course = Course.objects.get(pk=target.instance.id)
        course.events.count().should.be.equal(2)
        event1 = course.events.all()[1]
        event1.end_recurring_period.should.be.equal(next_occ.end)
