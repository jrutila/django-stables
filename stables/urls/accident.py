from django.conf.urls import *

from stables.views import CreateAccident

urlpatterns = patterns('',
    url(r'^add/', CreateAccident.as_view(), name="add_accident"),
)
