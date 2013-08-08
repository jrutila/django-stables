from django.conf.urls import *

from stables.views import Dashboard
from stables.views import ParticipationView

urlpatterns = patterns('',
    url(r'^dashboard/(?P<week>\d+)/$', Dashboard.as_view(), name="dashboard"),
    url(r'^dashboard/', Dashboard.as_view(), name="dashboard"),
    url(r'^participation/(?P<pk>\d+)/$', ParticipationView.as_view(), name="view_participation"),
)
