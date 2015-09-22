from django.conf.urls import patterns, url, include
# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()
from stables_shop.views import ParticipationPaymentRedirect, ParticipationPaymentSuccess, ParticipationPaymentNotify, \
    ParticipationPaymentFailure, NoShippingAddressCheckoutSelectionView, InfoView
from stables_shop.views import ParticipationPayment
from shop import urls as shop_urls

urlpatterns = patterns('',
    url('^pay/(?P<id>\d+)$', ParticipationPaymentRedirect.as_view(), name='shop-pay'),
    url('^pay/(?P<hash>\w+)$', ParticipationPayment.as_view(), name='shop-pay'),
    url('^pay/(?P<hash>\w+)/success$', ParticipationPaymentSuccess.as_view(), name='shop-pay-success'),
    url('^pay/(?P<hash>\w+)/notify$', ParticipationPaymentNotify.as_view(), name='shop-pay-notify'),
    url('^pay/(?P<hash>\w+)/failure$', ParticipationPaymentFailure.as_view(), name='shop-pay-failure'),
    url('^checkout/$', NoShippingAddressCheckoutSelectionView.as_view()),
    url('^info/$', InfoView.as_view(), name='shop-info'),
    url('^', include(shop_urls)),
)

