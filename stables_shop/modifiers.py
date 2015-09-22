from django.conf import settings

from shop.cart.cart_modifiers_base import BaseCartModifier
from django.utils.translation import ugettext_lazy as _
from decimal import *

class FixedVATRate(BaseCartModifier):
    """
    This will add 24% of the subtotal of the order to the total.

    It is of course not very useful in the real world, but this is an
    example.
    """

    def get_extra_cart_price_field(self, cart, request):
        getcontext().rounding = ROUND_HALF_UP
        taxes = settings.SHOP_VAT * cart.subtotal_price
        taxes = Decimal(format(taxes, '.2f'))
        to_append = (_('VAT'), taxes)
        return to_append
