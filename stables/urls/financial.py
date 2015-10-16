from django.conf.urls import *
from stables.views.financial import EditTransactionsView, AddTicketsView, EditTicketsView

urlpatterns = patterns('',
    url(r'^participation/(?P<pid>\d+)/transactions/$', EditTransactionsView.as_view(), name='modify_transactions'),
    url(r'^user/(?P<username>[\w\.]+)/addtickets/$', AddTicketsView.as_view(), name='add_tickets'),
    url(r'^user/(?P<username>[\w\.]+)/tickets/$', EditTicketsView.as_view(), name='edit_tickets'),
)
