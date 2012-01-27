from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^rider/(?P<username>\w+)$', 'stables.views.view_rider'),
    url(r'^customer/(?P<username>\w+)$', 'stables.views.view_customer'),
    url(r'^accounts/profile', 'stables.views.view_account'),
    # For staff
    url(r'^riderlevels', 'stables.views.update_rider_levels'),
)
