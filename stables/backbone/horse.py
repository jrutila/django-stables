from django.db.models import Q
from django.db.models.query import QuerySet
from tastypie import fields
from stables.backbone import ParticipationPermissionAuthentication
from tastypie.cache import SimpleCache
from tastypie.resources import ModelResource
from stables.models import Horse


class HorseQuerySet(QuerySet):
    def filter(self, *args, **kwargs):
        return super(HorseQuerySet, self).complex_filter(Q(Q(**kwargs) | Q(last_usage_date__isnull=True)))

class HorseResource(ModelResource):
    class Meta:
        queryset = HorseQuerySet(Horse, using=Horse.objects._db)
        cache = SimpleCache(timeout=30*60)
        authentication = ParticipationPermissionAuthentication()
        filtering = {
            'last_usage_date': ['gte'],
            }
    name = fields.CharField(attribute="name")
    day_limit = fields.IntegerField(attribute="day_limit", null=True)
    last_usage_date = fields.DateField(attribute="last_usage_date", null=True)

