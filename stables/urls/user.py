from django.conf.urls import *

from stables.views import AddUser

urlpatterns = patterns('',
    url(r'^user/add/', AddUser.as_view(), name="add_user"),
    url(r'^user/(?P<username>[\w\.]+)/$', 'stables.views.oldviews.view_user'),
    # For staff
    url(r'^riderlevels', 'stables.views.update_rider_levels'),
    url(r'^user/(?P<username>[\w\.]+)/addtickets/$', 'stables.views.add_tickets'),
)
