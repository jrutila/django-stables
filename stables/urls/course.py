from django.conf.urls import *

from stables.views import CourseCreate
from stables.views import CourseUpdate
from stables.views import CourseAddEvent

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/change/', CourseUpdate.as_view(), name="change_course"),
    url(r'^(?P<pk>\d+)/addevent/', CourseAddEvent.as_view(), name="add_event"),
    url(r'^(?P<course_id>\d+)/', 'stables.views.view_course'),
    url(r'^add/', CourseCreate.as_view(), name="add_course"),
)
