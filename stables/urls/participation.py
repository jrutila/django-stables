from django.conf.urls import *
from stables.views.dashboard import Newboard
from stables.views.participation import ParticipationView, DeleteEnroll, CreateEnroll, CancelView, AttendView, \
    DailyView


datetime_regex = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'

urlpatterns = patterns('',
    url(r'^newb/', Newboard.as_view(), name="newboard"),
    url(r'^participation/(?P<pk>\d+)/$', ParticipationView.as_view(), name="view_participation"),
    url(r'^enroll/(?P<pk>\d+)/$', DeleteEnroll.as_view(), name="delete_enroll"),
    url(r'^enroll/$', CreateEnroll.as_view(), name="create_enroll"),
    url(r'^(?P<event>\d+)/(?P<start>%s)/cancel/$' % datetime_regex, CancelView.as_view(), name="participation_cancel"),
    url(r'^(?P<pk>\d+)/cancel/$', CancelView.as_view(), name="participation_cancel"),
    url(r'^(?P<pk>\d+)/attend/$', AttendView.as_view(), name="participation_attend"),
    url(r'^daily/(?P<date>\d{4}-\d{2}-\d{2})/$', DailyView.as_view(), name='daily_view'),
)
