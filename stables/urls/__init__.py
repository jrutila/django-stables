from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^', include('stables.urls.old')),
    url(r'^c/', include('stables.urls.course')),
)
