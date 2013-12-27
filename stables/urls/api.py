from django.conf.urls import *

# from rest_framework import routers
from stables.api import TimetableView


urlpatterns = patterns('',
    url(r'^timetable/', TimetableView.as_view()),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
)
