from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^horse/add', 'stables.views.add_horse'),
    url(r'^course/(?P<course_id>\d+)/participations/(?P<occurrence_start>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', 'stables.views.modify_participations'),
    url(r'^course/(?P<course_id>\d+)/enrolls', 'stables.views.modify_enrolls'),
    url(r'^course/(?P<course_id>\d+)/attend/$', 'stables.views.attend_course'),
    url(r'^course/(?P<course_id>\d+)/enroll/$', 'stables.views.enroll_course'),
    url(r'^course/(?P<course_id>\d+)/cancel$', 'stables.views.cancel'),
    url(r'^course/(?P<course_id>\d+)$', 'stables.views.view_course'),
    url(r'^course$', 'stables.views.list_course'),
    url(r'^horse/(?P<horse_id>\d+)$', 'stables.views.view_horse'),
    url(r'^rider/(?P<username>\w+)$', 'stables.views.view_rider'),
    url(r'^customer/(?P<username>\w+)$', 'stables.views.view_customer'),
    url(r'^accounts/profile', 'stables.views.view_account'),
    url(r'^confirm/(?P<action>.*)$', 'stables.views.confirm'),
    # For staff
    url(r'^riderlevels', 'stables.views.update_rider_levels'),
)
