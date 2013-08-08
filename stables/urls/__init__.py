from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^', include('stables.urls.old')),
    url(r'^c/', include('stables.urls.course')),
    url(r'^u/', include('stables.urls.user')),
    url(r'^p/', include('stables.urls.participation')),
    url(r'^h/', include('stables.urls.horse')),
    url(r'^f/', include('stables.urls.financial')),
)
