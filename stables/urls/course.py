from django.conf.urls import *

from stables.views import CourseCreate
from stables.views import CourseUpdate
from stables.views import CourseAddEvent
from stables.views import CourseUpdateEvent
from stables.views import ViewCourse
from stables.views import ListCourse

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/change/', CourseUpdate.as_view(), name="change_course"),
    url(r'^(?P<pk>\d+)/addevent/', CourseAddEvent.as_view(), name="add_event"),
    url(r'^(?P<pk>\d+)/changeevent/(?P<start>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})/', CourseUpdateEvent.as_view(), name="change_event"),
    url(r'^(?P<pk>\d+)/', ViewCourse.as_view(), name='view_course'),
    url(r'^add/', CourseCreate.as_view(), name="add_course"),
    url(r'^$', ListCourse.as_view(), name='list_course'),
)
