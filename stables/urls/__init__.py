from django.conf.urls import *

import reporting
reporting.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('stables.urls.old')),
    url(r'^c/', include('stables.urls.course')),
    url(r'^u/', include('stables.urls.user')),
    url(r'^p/', include('stables.urls.participation')),
    url(r'^h/', include('stables.urls.horse')),
    url(r'^f/', include('stables.urls.financial')),
    url(r'^a/', include('stables.urls.accident')),
    url(r'^r/', include('reporting.urls')),
)