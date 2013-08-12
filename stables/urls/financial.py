from django.conf.urls import *

from stables.views import EditTransactionsView
from stables.views import AddTicketsView

urlpatterns = patterns('',
    url(r'^participation/(?P<pid>\d+)/transactions/$', EditTransactionsView.as_view(), name='modify_transactions'),
    url(r'^user/(?P<username>[\w\.]+)/addtickets/$', AddTicketsView.as_view(), name='add_tickets'),
)
