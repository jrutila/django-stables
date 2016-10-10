__author__ = 'jorutila'

#from shop.addressmodel.models import Address as BaseAddress
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings
from shop.models.address import BaseShippingAddress, BaseBillingAddress, ISO_3166_CODES

class AddressModelMixin(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    phone_number = models.CharField(_('Phone number'), max_length=255)

    class Meta:
        abstract = True
        app_label = "stables_shop"

class ShippingAddress(BaseShippingAddress, AddressModelMixin):
    class Meta:
        verbose_name = _("Shipping Address")
        verbose_name_plural = _("Shipping Addresses")
        app_label = "stables_shop"

class BillingAddress(BaseBillingAddress, AddressModelMixin):
    class Meta:
        verbose_name = _("Billing Address")
        verbose_name_plural = _("Billing Addresses")
        app_label = "stables_shop"
