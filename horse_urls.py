from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^(?P<horse_id>\d+)/$', 'stables.views.view_horse'),
    url(r'^$', 'stables.views.list_horse'),
)
