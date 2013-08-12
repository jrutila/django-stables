from django.conf.urls import *

from stables.views import AddUser
from stables.views import ListUser
from stables.views import ViewUser

urlpatterns = patterns('',
    url(r'^add/', AddUser.as_view(), name="add_user"),
    url(r'^(?P<username>[\w\.]+)/$', ViewUser.as_view(), name='view_user'),
    # For staff
    url(r'^riderlevels', 'stables.views.update_rider_levels'),
    url(r'^$', ListUser.as_view(), name='user-list'),
)
