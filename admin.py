from stables.models import Horse, Rider, Owner
from django.contrib import admin

import reversion

class HorseAdmin(reversion.VersionAdmin):
    pass

admin.site.register(Horse, HorseAdmin)
admin.site.register(Rider)
admin.site.register(Owner)
