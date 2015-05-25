from tastypie import fields
from tastypie.resources import Resource
from stables.backbone import ApiList
from stables.models import Course, ATTENDING
from stables.models.course import Enroll

__author__ = 'jorutila'

class ViewCourse:
    def __init__(self, course=None, enrolls=None):
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
            for dt in course.get_next_occurrences(amount=5):
                self.events.append(dt)

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

    def obj_get(self, bundle, **kwargs):
        id = kwargs['pk']
        c = Course.objects.get(pk=id)
        cc = ViewCourse(c, Enroll.objects.get_enrolls(c))
        return cc

