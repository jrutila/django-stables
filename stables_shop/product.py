from django.db import models
from django.utils.translation import ugettext_lazy as _
from shop.models_bases import BaseProduct

class Product(BaseProduct):
    class Meta:
        app_label = 'stables_shop'

    long_description = models.TextField(blank=True, null=True)

Product._meta.get_field('unit_price').help_text = _("The whole product price excluding VAT.")
