__author__ = 'jorutila'

#from shop.addressmodel.models import Address as BaseAddress
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings

BASE_ADDRESS_TEMPLATE = \
    _("""%(name)s
%(phone)s""")
ADDRESS_TEMPLATE = getattr(settings, 'SHOP_ADDRESS_TEMPLATE', BASE_ADDRESS_TEMPLATE)
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class Address(models.Model):
    user_shipping = models.OneToOneField(USER_MODEL, related_name='shipping_address',
                                         blank=True, null=True)
    user_billing = models.OneToOneField(USER_MODEL, related_name='billing_address',
                                        blank=True, null=True)

    name = models.CharField(_('Name'), max_length=255)
    phone_number = models.CharField(_('Phone number'), max_length=255)

    class Meta(object):
        verbose_name = _('Address')
        verbose_name_plural = _("Addresses")

    def __unicode__(self):
        return '%s (%s, %s)' % (self.name, self.zip_code, self.city)

    def clone(self):
        new_kwargs = dict([(fld.name, getattr(self, fld.name))
                           for fld in self._meta.fields if fld.name != 'id'])
        return self.__class__.objects.create(**new_kwargs)

    def as_text(self):
        return ADDRESS_TEMPLATE % {
            'name': self.name,
            'phone': self.phone_number,
            }
