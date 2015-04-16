from tastypie import fields
from stables.backbone import ParticipationPermissionAuthentication
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource
from stables.models.user import UserProfile


class UserResource(ModelResource):
    class Meta:
        queryset = UserProfile.objects.active()
        cache = SimpleCache(timeout=30*60)
        authentication = ParticipationPermissionAuthentication()
    name = fields.CharField()

    def dehydrate_name(self, bundle):
        return bundle.obj.user.first_name + " " + bundle.obj.user.last_name
