from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^horse/add', 'stables.views.add_horse'),
    url(r'^course/(?P<course_id>\d+)/attend$', 'stables.views.attend_course'),
    url(r'^course/(?P<course_id>\d+)/cancel$', 'stables.views.cancel_participation'),
    url(r'^course/(?P<course_id>\d+)', 'stables.views.view_course'),
    url(r'^course', 'stables.views.list_course'),
    url(r'^horse/(?P<horse_id>\d+)$', 'stables.views.view_horse'),
    url(r'^rider/(?P<username>\w+)$', 'stables.views.view_rider'),
)
