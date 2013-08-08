from django.conf.urls import *

from stables.views import EditTransactionsView

urlpatterns = patterns('',
    url(r'^participation/(?P<pid>\d+)/transactions/$', EditTransactionsView.as_view(), name='modify_transactions'),
)
