from django.conf.urls import *

from stables.views import ParticipationView
from stables.views import Newboard
from stables.views import CreateEnroll
from stables.views import DeleteEnroll

urlpatterns = patterns('',
    url(r'^newb/', Newboard.as_view(), name="newboard"),
    url(r'^participation/(?P<pk>\d+)/$', ParticipationView.as_view(), name="view_participation"),
    url(r'^enroll/(?P<pk>\d+)/$', DeleteEnroll.as_view(), name="delete_enroll"),
    url(r'^enroll/$', CreateEnroll.as_view(), name="create_enroll"),
)
