from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^user/$', 'stables.views.view_user'),
    url(r'^user/(?P<username>[\w\.]+)/$', 'stables.views.view_user'),
    # For staff
    url(r'^riderlevels', 'stables.views.update_rider_levels'),
    url(r'^user/(?P<username>[\w\.]+)/addtickets/$', 'stables.views.add_tickets'),
)
