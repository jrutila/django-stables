from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns, url
from django.db import models
from datetime import date
from django.core.urlresolvers import reverse
from shop.models import Product
from shop.models.defaults.order import Order
from shop.models.defaults.orderitem import OrderItem
from shop.shipping.backends.flat_rate import FlatRateShipping
from shop.shop_api import ShopAPI
from shop.util.decorators import on_method, order_required
from stables_shop import paytrail

class ProductActivator(models.Model):
    INITIATED = 10
    ACTIVATED = 20
    FAILED = 30
    CANCELED = 40

    STATUS_CODES = (
            (INITIATED, _('Initiated')),
            (ACTIVATED, _('Activated')),
            (FAILED, _('Failed')),
            (CANCELED, _('Canceled')),
            )
    product = models.ForeignKey(Product)
    order = models.ForeignKey(Order, related_name="activators")
    order_item = models.ForeignKey(OrderItem)
    status = models.IntegerField(choices=STATUS_CODES, default=INITIATED)

class DigitalShipping(FlatRateShipping):
    backend_name = 'digital'
    verbose_name = _('Digital')
    url_namespace = 'digital'

    def __init__(self, shop):
        self.shop = shop
        self.rate = 0

    def redirect(self, request):
        return self.shop.finished(self.shop.get_order(request))

    def get_urls(self):
        urlpatterns = patterns('',
                url(r'^$', self.redirect, name='digital'),
        )
        return urlpatterns

    def ship(self, order):
        for oi in order.items.all():
            for x in range(0, oi.quantity):
                product = oi.product
                if hasattr(product, 'get_activator'):
                    activator = product.get_activator()
                    activator.product = product
                    activator.order_item = oi
                    activator.order = order
                    activator.save()
                    activator.activate()
        order.status = Order.SHIPPED
        order.save()

def is_shipped(self):
    return self.status == Order.SHIPPED
    #act_count = self.activators.count()
    #return act_count >= 0 and self.activators.filter(status=ProductActivator.ACTIVATED).count() == act_count

Order.is_shipped = is_shipped

class PayTrailBackend(object):
    url_namespace='paytrail-payment'
    backend_name = _('Paytrail payment')
    template = 'shop/paytrail-payment-notify.html'

    def __init__(self, shop):
        self.shop = shop

    def get_urls(self):
        urlpatterns = patterns('',
                url(r'^$', self.paytrail_payment_view, name='paytrail-payment'),
                url(r'^success$', self.paytrail_payment_success, name='paytrail-success'),
                url(r'^notify$', self.paytrail_payment_notify, name='paytrail-notify'),
                url(r'^failure$', self.paytrail_payment_failure, name='paytrail-failure'),
                               )
        return urlpatterns

    @on_method(order_required)
    def paytrail_payment_view(self, request):
        order = self.shop.get_order(request)
        amount = self.shop.get_order_total(order)
        transaction_id = date.today().strftime('%Y') + '%06d' % order.id
        urls = {
            'success': request.build_absolute_uri(reverse('paytrail-success')),
            'notification': request.build_absolute_uri(reverse('paytrail-notify')),
            'failure': request.build_absolute_uri(reverse('paytrail-failure')),
            'pending': ''
                }
        redirect_url = paytrail.createPayment(order, amount, order.id, urls)
        order.status = Order.CONFIRMING
        order.save()
        return redirect(redirect_url)

    def _check_authcode(self, request):
        order_number = request.GET.get('ORDER_NUMBER')
        timestamp = request.GET.get('TIMESTAMP')
        paid = request.GET.get('PAID')
        method = request.GET.get('METHOD')
        authCode = paytrail.calcAuthCode(order_number, timestamp, paid, method)
        if authCode != request.GET.get('RETURN_AUTHCODE').lower():
            raise Exception("Authcode mismatch!")
        return order_number

    def paytrail_payment_success(self, request):
        order_number = self._check_authcode(request)
        order = Order.objects.get(pk=order_number)
        order.status = Order.CONFIRMED
        order.save()
        return HttpResponseRedirect(self.shop.get_finished_url())

    def paytrail_payment_failure(self, request):
        order_number = self._check_authcode(request)
        order = Order.objects.get(pk=order_number)
        order.status = Order.CANCELED
        order.save()
        return HttpResponseRedirect(self.shop.get_cancel_url())

    def paytrail_payment_notify(self, request):
        method = request.GET.get('METHOD')
        order_number = self._check_authcode(request)
        order = Order.objects.get(pk=order_number)
        ShopAPI.PaymentAPI().confirm_payment(order, order.order_total, order.id, method)
        return HttpResponse("ok")
