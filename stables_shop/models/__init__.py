from django.core.validators import MinValueValidator
from django.db.models import IntegerField
from shop.models.customer import BaseCustomer
from shop.models.cart import BaseCartItem  # nopyflakes
#from shop.models.defaults.cart import Cart  # nopyflakes
from shop.models.cart import BaseCart  # nopyflakes
from shop.models.address import BaseShippingAddress  # nopyflakes
from shop.models.order import BaseOrder # nopyflakes
from shop.models.order import BaseOrderItem # nopyflakes
from django.db import models
from shop import deferred
from addressmodel import AddressModelMixin, ShippingAddress # nopyflakes
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.utils import timezone

class Customer(BaseCustomer):
    class Meta:
        app_label = "stables_shop"

class CartItem(BaseCartItem):
    """Default materialized model for CartItem"""
    quantity = IntegerField(validators=[MinValueValidator(0)])

class Cart(BaseCart):
    """
    Default materialized model for BaseCart containing common fields
    """
    #class Meta:
        #app_label = "stables_shop"
    shipping_address = deferred.ForeignKey('BaseShippingAddress', null=True, default=None, related_name='+')

class Order(BaseOrder):
    """Default materialized model for Order"""
    number = models.PositiveIntegerField(_("Order Number"), null=True, default=None, unique=True)
    shipping_address_text = models.TextField(_("Shipping Address"), blank=True, null=True,
                                             help_text=_("Shipping address at the moment of purchase."))

    class Meta:
        verbose_name = pgettext_lazy('order_models', "Order")
        verbose_name_plural = pgettext_lazy('order_models', "Orders")

    def get_or_assign_number(self):
        """
        Set a unique number to identify this Order object. The first 4 digits represent the
        current year. The last five digits represent a zero-padded incremental counter.
        """
        if self.number is None:
            epoch = timezone.now().date()
            epoch = epoch.replace(epoch.year, 1, 1)
            aggr = Order.objects.filter(number__isnull=False, created_at__gt=epoch).aggregate(models.Max('number'))
            try:
                epoc_number = int(str(aggr['number__max'])[4:]) + 1
                self.number = int('{0}{1:05d}'.format(epoch.year, epoc_number))
            except (KeyError, ValueError):
                # the first order this year
                self.number = int('{0}00001'.format(epoch.year))
        return self.get_number()

    def get_number(self):
        return '{0}-{1}'.format(str(self.number)[:4], str(self.number)[4:])

    def populate_from_cart(self, cart, request):
        self.shipping_address_text = cart.shipping_address.as_text()
        self.billing_address_text = cart.billing_address.as_text() if cart.billing_address else self.shipping_address_text
        super(Order, self).populate_from_cart(cart, request)

class OrderItem(BaseOrderItem):
    """Default materialized model for OrderItem"""
    quantity = models.IntegerField(_("Ordered quantity"))

    def populate_from_cart_item(self, cart_item, request):
        # The optional attribute `product.product_code` might be missing, if for instance
        # it is implemented through a product variation. In this case replace this method
        # by it's own business logic.
        self.product_code = cart_item.product.product_code
        super(OrderItem, self).populate_from_cart_item(cart_item, request)
