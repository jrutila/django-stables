from django.contrib.sites.models import Site
from django_comments.models import Comment
from schedule.models import Event
from tastypie import fields
from tastypie.bundle import Bundle
from stables.backbone import ParticipationPermissionAuthentication
from tastypie.authorization import Authorization
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField
from tastypie.resources import ModelResource
from stables.models.event_metadata import EventMetaData

__author__ = 'jorutila'

class EventMetaDataResource(ModelResource):
    class Meta:
        queryset  = EventMetaData.objects.all()
        object_class = EventMetaData
        authorization= Authorization()
        always_return_data = True
        authentication = ParticipationPermissionAuthentication()
    event = fields.ForeignKey("stables.backbone.EventResource", attribute='event')

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj
        return { 'pk': bundle_or_obj.id }

class CommentResource(ModelResource):
    content_object = GenericForeignKeyField({
                                                EventMetaData: EventMetaDataResource,
                                                }, 'content_object')

    class Meta:
        queryset = Comment.objects.all()
        model = Comment
        authorization = Authorization()
        filtering = {
            'content_object': [ 'exact', ]
        }
        always_return_data = True
        authentication = ParticipationPermissionAuthentication()

    def detail_uri_kwargs(self, bundle_or_obj):
        if isinstance(bundle_or_obj, Bundle):
            bundle_or_obj = bundle_or_obj.obj
        return { 'pk': bundle_or_obj.id }

    def hydrate_content_object(self, bundle):
        obj = bundle.data['content_object']
        # TODO: There has to be better way!
        if isinstance(obj, dict):
            if 'id' not in obj:
                obj['event'] = int(obj['event'].split('/')[-2])
                obj['event'] = Event.objects.get(pk=obj['event'])
            else:
                pk = obj['id']
                obj = { 'id': pk }
        else:
            pk = int(obj.split('/')[-2])
            obj = { 'id': pk }
        bundle.data['content_object'] = EventMetaData.objects.get_or_create(**obj)[0]
        return bundle

    def obj_create(self, bundle, **kwargs):
        kwargs['site'] = Site.objects.get_current()
        return super(CommentResource, self).obj_create(bundle, **kwargs)
