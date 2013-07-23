from django.conf.urls import *

from stables.views import CourseCreate
from stables.views import CourseUpdate

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/change/', CourseUpdate.as_view(), name="change_course"),
    url(r'^(?P<course_id>\d+)/', 'stables.views.view_course'),
    url(r'^add/', CourseCreate.as_view(), name="add_course"),
)
