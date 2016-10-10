from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DurationField
from stables.models.course import Course, Enroll
from stables.models.financial import TicketType, Ticket
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from stables.models.participations import Participation
from stables.models.user import RiderInfo, UserProfile
from django.utils import timezone
import datetime
from django_settings.models import Model as SettingsModel
from django_settings.models import registry
from django.core.urlresolvers import reverse
from ..backends import ProductActivator
from ..markov_passwords import MarkovChain, finnish
from ..templatetags.stables_shop_tags import add_vat
from .product import Product
#from discount.default_discounts.models import CartItemAbsoluteDiscount, CartItemPercentDiscount, PercentDiscount

class LongString(SettingsModel):
   value = models.TextField()

   class Meta:
       abstract = True
       app_label = "stables_shop"
registry.register(LongString)

class DigitalShippingAddressModel(models.Model):
    name = models.TextField()

    def as_text(self):
        return self.name

def _getUserName(address):
    return address.split('\n')[0]

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Ticket)
def ticket_expirer(sender, **kwargs):
    ticket = kwargs['instance']
    if ticket.transaction and not ticket.expires:
        actr = TicketProductActivator.objects.filter(start__lte=ticket.id, end__gte=ticket.id)
        if actr:
            actr = actr[0]
            exp = datetime.datetime.combine(
                    ticket.transaction.source.start.date()+actr.duration,
                    datetime.time(23,59,59))
            Ticket.objects.filter(id__gte=actr.start, id__lte=actr.end).update(expires=exp)

def check_active(sender, instance, created, **kwargs):
    return
    if instance.course.is_full():
        EnrollProduct.objects.filter(course=instance.course).update(active=False)
    elif instance.course.get_occurrences()[0].start < timezone.now():
        EnrollProduct.objects.filter(course=instance.course).update(active=False)
    else:
        EnrollProduct.objects.filter(course=instance.course).update(active=True)

from django.db.models.signals import post_save
post_save.connect(check_active, sender=Enroll)

def get_short_url_for(partid, create=False):
     shortUrl = PartShortUrl.objects.filter(participation=partid)
     if shortUrl.count() == 0 and create:
         PartShortUrl.objects.create(participation=Participation.objects.get(pk=partid))
         shortUrl = PartShortUrl.objects.filter(participation=partid)
     if shortUrl.count() == 1:
         return reverse('shop-pay', kwargs={ 'hash': shortUrl[0].hash })
     return reverse('shop-pay', kwargs={ 'id': partid })

import string
chain = MarkovChain(c for c in finnish.lower() if c in string.ascii_lowercase)

class ProductAbsoluteDiscount(models.Model): #CartItemAbsoluteDiscount):
    products = models.ManyToManyField(Product)
    product_filters = []

    def get_products(self):
        return self.products.all()

    def __str__(self):
        return "%s (%s e)" % (self.name, str(add_vat(self.amount))) # str(Decimal(self.amount*(1+settings.SHOP_VAT)).quantize(Decimal('0.00'))))

class ProductPercentDiscount(models.Model): #CartItemPercentDiscount):
    products = models.ManyToManyField(Product)
    product_filters = []

    def get_products(self):
        return self.products.all()

    def __str__(self):
        return "%s (%s prosenttia)" % (self.name, self.amount)

class WholePercentDiscount(models.Model): #PercentDiscount):
    def __str__(self):
        return "%s (%s prosenttia)" % (self.name, self.amount)
