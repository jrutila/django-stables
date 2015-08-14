import datetime
from schedule.models import Event
from stables.models.user import UserProfile
from tastypie import fields
from stables.backbone import ParticipationPermissionAuthentication
from tastypie.resources import ModelResource
from stables.models import Enroll

__author__ = 'jorutila'

class EnrollResource(ModelResource):
    class Meta:
        resource_name = 'enroll'
        object_class = Enroll
        list_allowed_methods = ['post', 'put']
        authentication = ParticipationPermissionAuthentication()
        always_return_data = True

    event = fields.IntegerField()

    def obj_create(self, bundle, request=None, **kwargs):
        part = UserProfile.objects.get(pk=bundle.data['rider'])
        event = Event.objects.get(pk=bundle.data['event'])
        enroll = Enroll.objects.get_or_create(course=event.course_set.all()[0], participant=part)[0]
        enroll.state = 0
        enroll.last_state_change_on = datetime.datetime.now()
        enroll.save()
        bundle.obj = enroll
        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        enroll = Enroll.objects.get(pk=kwargs['pk'])
        enroll.state = bundle.data['state']
        enroll.last_state_change_on = datetime.datetime.now()
        enroll.save()
        bundle.obj = enroll
        return bundle
