from django.conf.urls import *

from tastypie.api import Api
from stables.backbone import *

v1_api = Api(api_name="v1")
v1_api.register(UserResource())
v1_api.register(ParticipationResource())
v1_api.register(EventResource())
v1_api.register(CommentResource())
v1_api.register(EventMetaDataResource())
v1_api.register(EnrollResource())
v1_api.register(FinanceResource())
v1_api.register(HorseResource())
v1_api.register(PaymentLinkResource())

import reportengine
reportengine.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('stables.urls.old')),
    url(r'^c/', include('stables.urls.course')),
    url(r'^u/', include('stables.urls.user')),
    url(r'^p/', include('stables.urls.participation')),
    url(r'^h/', include('stables.urls.horse')),
    url(r'^f/', include('stables.urls.financial')),
    url(r'^a/', include('stables.urls.accident')),
    url(r'^r/', include('reportengine.urls')),
    url(r'^backbone/', include(v1_api.urls)),
    url(r'^api/', include('stables.urls.api')),
)

from django.conf import settings
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
