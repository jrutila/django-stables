from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _

# DEPRECATED
class StablesApphook(CMSApp):
    name = _("Deprecated stables apphook")
    urls = ["stables.urls"]

apphook_pool.register(StablesApphook)

class CourseApphook(CMSApp):
    name = _("Courses Apphook")
    urls = ["stables.urls"]

apphook_pool.register(CourseApphook)

class HorseApphook(CMSApp):
    name = _("Horse Apphook")
    urls = ["stables.horse_urls"]

apphook_pool.register(HorseApphook)

class UserApphook(CMSApp):
    name = _("User Apphook")
    urls = ["stables.user_urls"]

apphook_pool.register(UserApphook)

class ScheduleApphook(CMSApp):
    name = _("Schedule apphook")
    urls = ["schedule.urls"]

apphook_pool.register(ScheduleApphook)
