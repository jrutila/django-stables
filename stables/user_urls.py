from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^user/(?P<username>\w+)/$', 'stables.views.view_user'),
    url(r'^accounts/profile', 'stables.views.view_account'),
    # For staff
    url(r'^riderlevels', 'stables.views.update_rider_levels'),
    url(r'^user/(?P<username>\w+)/addtickets/$', 'stables.views.add_tickets'),
)
