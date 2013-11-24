from django.conf.urls import *

from stables.views import CreateAccident
from stables.views import EditAccident

urlpatterns = patterns('',
    url(r'^add/', CreateAccident.as_view(), name="add_accident"),
    url(r'^(?P<pk>\d+)', EditAccident.as_view(), name="edit_accident"),
)
