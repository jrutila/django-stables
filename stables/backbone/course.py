from tastypie import fields
from tastypie.resources import Resource
from stables.models import Course

__author__ = 'jorutila'

class ViewCourse:
    def __init__(self, course=None):
        if course:
            self.id = course.id
            self.name = course.name
            self.max_participants = course.max_participants
            self.default_participation_fee = course.default_participation_fee

class CourseResource(Resource):
    class Meta:
        resource_name = 'courses'
        object_class = ViewCourse
        list_allowed_methods = ['get']

    id = fields.CharField(attribute='id')
    name = fields.CharField(attribute='name')
    max_participants = fields.IntegerField(attribute='max_participants', null=True)
    default_participation_fee = fields.DecimalField(attribute='default_participation_fee', null=True)

    def obj_get(self, bundle, **kwargs):
        id = kwargs['pk']
        c = Course.objects.get(pk=id)
        cc = ViewCourse(c)
        return cc

