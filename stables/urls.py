from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^(?P<course_id>\d+)/participations/(?P<occurrence_start>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/', 'stables.views.modify_participations'),
    url(r'^(?P<course_id>\d+)/horses/(?P<occurrence_start>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/', 'stables.views.modify_participation_horses'),
    url(r'^(?P<course_id>\d+)/time/(?P<occurrence_start>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/', 'stables.views.modify_participation_time'),
    url(r'^(?P<course_id>\d+)/enrolls/$', 'stables.views.modify_enrolls'),
    url(r'^(?P<course_id>\d+)/attend/$', 'stables.views.attend_course'),
    url(r'^(?P<course_id>\d+)/enroll/$', 'stables.views.enroll_course'),
    url(r'^(?P<course_id>\d+)/cancel/$', 'stables.views.cancel'),
    url(r'^(?P<course_id>\d+)/$', 'stables.views.view_course'),
    url(r'^dashboard/$', 'stables.views.dashboard'),
    url(r'^daily/$', 'stables.views.daily'),
    url(r'^daily/(?P<date>\d{4}-\d{2}-\d{2})/$', 'stables.views.daily'),
    url(r'^dashboard/(?P<week>\d+)/$', 'stables.views.dashboard'),
    url(r'^$', 'stables.views.list_course'),
    url(r'^confirm/(?P<action>.*)/$', 'stables.views.confirm'),
)
