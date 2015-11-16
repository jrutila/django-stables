from django.contrib.auth.backends import ModelBackend
from tenant_schemas.utils import get_public_schema_name
from tenant_schemas.utils import get_tenant_model
from tenant_schemas.utils import tenant_context

def fake_public_tenant():
    return get_tenant_model()(schema_name=get_public_schema_name(), id=1)

class MasterUserBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        with tenant_context(fake_public_tenant()):
            ret = super(MasterUserBackend, self).authenticate(username, password)
        return ret

    def get_user(self, user_id):
        with tenant_context(fake_public_tenant()):
            ret = super(MasterUserBackend, self).get_user(user_id)
        return ret
