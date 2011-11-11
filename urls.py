from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^horse/add', 'stables.views.add_horse'),
    url(r'^horse/(?P<horse_id>\d+)$', 'stables.views.view_horse'),
)
