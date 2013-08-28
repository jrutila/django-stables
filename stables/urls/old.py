from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^(?P<course_id>\d+)/enrolls/$', 'stables.views.modify_enrolls'),
    url(r'^(?P<course_id>\d+)/attend/$', 'stables.views.attend_course'),
    url(r'^(?P<course_id>\d+)/enroll/$', 'stables.views.enroll_course'),
    url(r'^(?P<course_id>\d+)/cancel/$', 'stables.views.cancel'),
    url(r'^(?P<course_id>\d+)/skip/$', 'stables.views.skip'),
    url(r'^pay/$', 'stables.views.pay'),
    url(r'^widget/$', 'stables.views.widget'),
    url(r'^widget/(?P<date>\d{4}-\d{2}-\d{2})/$', 'stables.views.widget'),
    url(r'^daily/$', 'stables.views.daily'),
    url(r'^daily/(?P<date>\d{4}-\d{2}-\d{2})/$', 'stables.views.daily'),
    url(r'^week/(?P<week>\d+)/$', 'stables.views.list_course'),
    url(r'^$', 'stables.views.list_course'),
    url(r'^confirm/(?P<action>.*)/$', 'stables.views.confirm'),
)