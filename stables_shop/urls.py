from django.conf.urls import patterns, url
# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()
from django.core.urlresolvers import reverse_lazy

from discount.views import CartDiscountCodeCreateView, CartDiscountCodeDeleteView
from stables_shop.views import HomePageView, PayView, ShipView, EditProduct, CreateProduct, FinishedOrderList, \
    SettingsView, EditDiscount, CreateDiscount

urlpatterns = patterns('',
    url(r'^$', HomePageView.as_view(), name='shop-home'),
    url(r'^paid/', PayView.as_view(), name='order-paid'),
    url(r'^ship/', ShipView.as_view(), name='order-ship'),
    url(r'^product/(?P<pk>\d+)/edit/', EditProduct.as_view(), name='product-edit'),
    url(r'^product/add/(?P<content_type_id>\d+)', CreateProduct.as_view(), name='product-add'),
    url(r'^discount/(?P<pk>\d+)/edit/', EditDiscount.as_view(), name='discount-edit'),
    url(r'^discount/add/(?P<content_type_id>\d+)', CreateDiscount.as_view(), name='discount-add'),
    url(r'^order/', FinishedOrderList.as_view(), name='order-list'),
    url(r'^settings/', SettingsView.as_view(), name='shop-settings'),
)

CartDiscountCodeCreateView.success_url = reverse_lazy('cart')
CartDiscountCodeDeleteView.success_url = reverse_lazy('cart')
