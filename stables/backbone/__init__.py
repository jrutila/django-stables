import logging
import pickle

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
        logger.debug("ShortClientCache save %s" % key)
        if isinstance(value, list):
            logger.debug("Iterate over value")
            for val in value:
                logger.debug(getattr(val, "title", "NO TITLE"))
                pickled = pickle.dumps(val, pickle.HIGHEST_PROTOCOL)
        super().set(key, value, timeout)
