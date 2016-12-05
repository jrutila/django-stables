from django.conf.urls import *
from rest_framework import routers

# from rest_framework import routers
from stables.api import TimetableView
from stables.api import ParticipationViewSet

router = routers.DefaultRouter()
router.register(r'participations', ParticipationViewSet, 'participation')

urlpatterns = router.urls + [
 url(r'^timetable/', TimetableView.as_view(), name="timetable"),
 url(r'^', include(router.urls)),
]
