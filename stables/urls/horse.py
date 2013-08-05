from django.conf.urls import *

from stables.views import HorseCreate
from stables.views import HorseUpdate
from stables.views import ViewHorse
from stables.views import HorseList

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/change/', HorseUpdate.as_view(), name="change_horse"),
    url(r'^add/', HorseCreate.as_view(), name="add_horse"),
    #url(r'^(?P<pk>\d+)/addevent/', HorseAddEvent.as_view(), name="add_horse"),
    #url(r'^(?P<pk>\d+)/changeevent/(?P<start>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/', CourseUpdateEvent.as_view(), name="change_event"),
    url(r'^(?P<pk>\d+)/', ViewHorse.as_view(), name='view_horse'),
    url(r'', HorseList.as_view(), name='list_horse'),
)
