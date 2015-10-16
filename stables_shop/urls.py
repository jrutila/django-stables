from django.conf.urls import patterns, url
# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()
from stables_shop.views import HomePageView, PayView, ShipView, EditProduct, CreateProduct, FinishedOrderList, \
    SettingsView

urlpatterns = patterns('',
    url(r'^$', HomePageView.as_view(), name='shop-home'),
    url(r'^paid/', PayView.as_view(), name='order-paid'),
    url(r'^ship/', ShipView.as_view(), name='order-ship'),
    url(r'^product/(?P<pk>\d+)/edit/', EditProduct.as_view(), name='product-edit'),
    url(r'^product/add/(?P<content_type_id>\d+)', CreateProduct.as_view(), name='product-add'),
    url(r'^order/', FinishedOrderList.as_view(), name='order-list'),
    url(r'^settings/', SettingsView.as_view(), name='shop-settings'),
)

