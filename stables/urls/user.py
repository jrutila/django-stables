from django.conf.urls import *

from stables.views import AddUser

urlpatterns = patterns('',
    url(r'^adduser/', AddUser.as_view(), name="add_user"),
)
