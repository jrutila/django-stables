from django.conf.urls import *
from rest_framework import routers

# from rest_framework import routers
from stables.api import TimetableView

router = routers.DefaultRouter()

urlpatterns = router.urls + [
 url(r'^timetable/', TimetableView.as_view(), name="timetable"),
]
