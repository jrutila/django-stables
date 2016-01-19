#from shop.models import Product
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DurationField

from discount.default_discounts.models import CartItemAbsoluteDiscount, CartItemPercentDiscount, PercentDiscount
from shop.models import Product
from shop.models_bases import BaseProduct
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
from stables_shop.backends import ProductActivator
from stables_shop.markov_passwords import MarkovChain, finnish
from stables_shop.templatetags.stables_shop_tags import add_vat


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

class TicketProductActivator(ProductActivator):
    start = models.PositiveIntegerField(null=True)
    end = models.PositiveIntegerField(null=True)
    rider = models.ForeignKey(RiderInfo, null=True, blank=True)
    duration = DurationField(blank=True, null=True)

    def activate(self):
        user = UserProfile.objects.find(_getUserName(self.order.shipping_address_text))
        if user:
            self.rider = user.rider
            for i in range(0, self.product.amount):
                exp = None
                if self.product.expires:
                    exp = self.product.expires
                t = Ticket.objects.create(
                        type=self.product.ticket,
                        owner=self.rider,
                        expires=exp)
                if i == 0: self.start = t.id
                if i == self.product.amount-1: self.end = t.id
            self.duration = self.product.duration
            self.status = self.ACTIVATED
            self.save()

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

class EnrollProduct(Product):
    course = models.ForeignKey(Course)
    automatic_disable = models.BooleanField()

    class Meta:
        pass

    def get_activator(self):
        return EnrollProductActivator()

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

class EnrollProductActivator(ProductActivator):
    rider = models.ForeignKey(RiderInfo, null=True, blank=True)

    def activate(self):
        user = UserProfile.objects.find(_getUserName(self.order.shipping_address_text))

        if user:
            self.rider = user.rider
            self.product.course.enroll(user)
            self.status = self.ACTIVATED
            self.save()

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

def generate_hash():
    import itertools
    hash = ''.join(itertools.islice(chain, 12))
    return hash

class PartShortUrl(models.Model):
    participation = models.ForeignKey(Participation, unique=True)
    hash = models.CharField(unique=True, max_length=12, default=generate_hash)

    def __str__(self):
        return "%s - %s" % (self.hash, self.participation)

class ProductAbsoluteDiscount(CartItemAbsoluteDiscount):
    products = models.ManyToManyField(Product)
    product_filters = []

    def get_products(self):
        return self.products.all()

    def __str__(self):
        return "%s (%s e)" % (self.name, str(add_vat(self.amount))) # str(Decimal(self.amount*(1+settings.SHOP_VAT)).quantize(Decimal('0.00'))))

class ProductPercentDiscount(CartItemPercentDiscount):
    products = models.ManyToManyField(Product)
    product_filters = []

    def get_products(self):
        return self.products.all()

    def __str__(self):
        return "%s (%s prosenttia)" % (self.name, self.amount)

class WholePercentDiscount(PercentDiscount):
    def __str__(self):
        return "%s (%s prosenttia)" % (self.name, self.amount)
