from django.db import models
from django.utils.translation import ugettext_lazy as _
from shop.models.product import BaseProduct, BaseProductManager
from stables.models.financial import TicketType, Ticket
from django.db.models import DurationField
from stables.models.course import Course, Enroll

class ProductManager(BaseProductManager):
  pass

class Product(BaseProduct):
    product_name = models.TextField(max_length=255)
    unit_price = models.DecimalField(decimal_places=3, max_digits=7, help_text=_("The whole product price excluding VAT."))
    slug = models.SlugField(verbose_name=_("Slug"))
    caption = models.TextField(max_length=255)

    def __unicode__(self):
        return self.product_name

    def get_absolute_url(self):
        return "ANKKA"

    def get_price(self, request):
        return self.unit_price

    objects = BaseProductManager()
    class Meta:
        app_label = 'stables_shop'

    lookup_fields = ('product_name', )

    long_description = models.TextField(blank=True, null=True)

class TicketProduct(Product):
    ticket = models.ForeignKey(TicketType)
    amount = models.PositiveIntegerField(help_text=_("Amount of tickets included in this product."))
    duration = DurationField(blank=True, null=True, help_text=_("Relative duration of the given product. For example 30 days, 90 days. If this is empty, you must insert expire date."))
    expires = models.DateField(blank=True, null=True, help_text=_("Absolute expiration date for the given product. For example 2014-12-31. If this is empty, you must insert duration."))

    class Meta:
        pass

    def clean(self):
        if not(self.duration or self.expires):
            raise ValidationError(_("Ticket duration or absolute expire date must be set"))

    def get_activator(self):
        return TicketProductActivator()

class EnrollProduct(Product):
    course = models.ForeignKey(Course)
    automatic_disable = models.BooleanField()

    class Meta:
        pass

    def get_activator(self):
        return EnrollProductActivator()

