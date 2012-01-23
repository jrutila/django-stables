from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

class StablesApphook(CMSApp):
    name = _("Stables Apphook")
    urls = ["stables.urls"]

apphook_pool.register(StablesApphook)
