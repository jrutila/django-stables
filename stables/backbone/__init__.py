import logging

from tastypie.cache import SimpleCache
from tastypie.authentication import SessionAuthentication
from django.db import connection

logger = logging.getLogger(__name__)

class ParticipationPermissionAuthentication(SessionAuthentication):
    def is_authenticated(self, request, **kwargs):
        return request.user.has_perm('stables.change_participation')

class ApiList(list):
    def all(self):
        return self

class ShortClientCache(SimpleCache):
    def cache_control(self):
        control = super(ShortClientCache, self).cache_control()
        control['max-age'] = 0
        control['s-maxage'] = 0
        control['no-cache'] = True
        control['no-store'] = True
        control['must-revalidate'] = True
        return control

    def get(self, key, **kwargs):
        key = connection.get_schema() +  ":" + key
        return super().get(key, **kwargs)

    def set(self, key, value, timeout=None):
        key = connection.get_schema() +  ":" + key
        super().set(key, value, timeout)
