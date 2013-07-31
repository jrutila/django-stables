from django.conf.urls import *

from stables.views import Dashboard

urlpatterns = patterns('',
    url(r'^dashboard/(?P<week>\d+)/$', Dashboard.as_view(), name="dashboard"),
    url(r'^dashboard/', Dashboard.as_view(), name="dashboard"),
)
