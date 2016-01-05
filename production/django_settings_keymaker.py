from django.db import connection
from django_settings.keymaker import KeyMaker

class TenantKeyMaker(KeyMaker):
    def make(self, method_name, args, kwargs):
        key = super().make(method_name, args, kwargs)
        key = connection.get_schema()+":"+key
        return key