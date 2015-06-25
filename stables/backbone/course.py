from tastypie import fields
from tastypie.resources import Resource
from stables.backbone import ApiList
from stables.models import Course, ATTENDING
from stables.models import Participation
from stables.models.course import Enroll
from django.utils.dateparse import parse_datetime
from django.utils import timezone

__author__ = 'jorutila'

class ViewCourse:
    def __init__(self, course=None, enrolls=None, participations=None):
        if course:
            self.id = course.id
            self.name = course.name
            self.max_participants = course.max_participants
            self.default_participation_fee = course.default_participation_fee
            self.enrolls = ApiList()
            for e in enrolls:
                if e.state == ATTENDING:
                    self.enrolls.append(e.participant)
            self.events = ApiList()
            for dt in course.get_next_occurrences(amount=6):
                self.events.append(dt)
            self.participations = ApiList()
            for p in participations:
                self.participations.append({
                    "id"          : p.id,
                    "participant" : p.participant,
                    "state"       : p.state,
                    "start"       : p.start
                })

class CourseResource(Resource):
    class Meta:
        resource_name = 'courses'
        object_class = ViewCourse
        list_allowed_methods = ['get']

    id = fields.CharField(attribute='id')
    name = fields.CharField(attribute='name')
    max_participants = fields.IntegerField(attribute='max_participants', null=True)
    default_participation_fee = fields.DecimalField(attribute='default_participation_fee', null=True)
    enrolls = fields.ListField(attribute='enrolls')
    events = fields.ListField(attribute='events')
    participations = fields.ListField(attribute='participations')

    def obj_get(self, bundle, **kwargs):
        id = kwargs['pk']
        c = Course.objects.get(pk=id)
        p = Participation.objects.filter(event__course=id, start__gte=timezone.now()).order_by("-start")
        cc = ViewCourse(c, Enroll.objects.get_enrolls(c), p)
        return cc

    def obj_update(self, bundle, request=None, **kwargs):
        id = kwargs['pk']
        c = Course.objects.get(pk=id)
        event = bundle.data["newEvent"]
        start = parse_datetime(event["date"]+" "+event["start"])
        end = parse_datetime(event["date"]+" "+event["end"])
        end_recurring_period = parse_datetime(event["repeatUntil"]+" "+event["end"])
        start = timezone.get_current_timezone().localize(start)
        end = timezone.get_current_timezone().localize(end)
        nEvent = {
            "start": start,
            "end": end,
            "end_recurring_period": end_recurring_period
        }

        c.name = bundle.data["name"]
        if ("newEvent" in bundle.data
          and "repeat" in bundle.data["newEvent"]
          and bundle.data["newEvent"]["repeat"]):
            c.setRecurrentEvent(**nEvent)
        else:
            c.addEvent(**nEvent)
        c.save()
        cc = ViewCourse(c, Enroll.objects.get_enrolls(c))
        return cc
