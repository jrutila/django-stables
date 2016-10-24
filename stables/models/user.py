from functools import reduce
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
import operator
from phonenumber_field.modelfields import PhoneNumberField
from stables.models.common import CustomerInfo

class UserManager(models.Manager):
    def get_query_set(self):
        return models.QuerySet(self.model, using=self._db).prefetch_related('user')

    def active(self):
        return self.get_query_set().filter(inactive=False).filter(Q(rider__isnull=False) | Q(customer__isnull=False))

    def find(self, name):
        f = []

        user = UserProfile.objects.filter(
                user__first_name=name.split(' ')[0],
                user__last_name=' '.join(name.split(' ')[1:])
                )
        if user:
            return user[0]
        for v in name.split(" "):
            f.append((Q(user__first_name__icontains=v) | Q(user__last_name__icontains=v)))
        return UserProfile.objects.get(reduce(operator.and_, f))

class RiderLevel(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return self.name
    name = models.CharField(max_length=30)
    includes = models.ManyToManyField('self', null=True, blank=True, symmetrical=False)

class UserProfile(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return self.user.first_name + ' ' + self.user.last_name
    objects = UserManager()
    user = models.OneToOneField("auth.User")
    rider = models.OneToOneField('RiderInfo', null=True, blank=True, related_name='user', on_delete=models.SET_NULL)
    customer = models.OneToOneField('CustomerInfo', null=True, blank=True, on_delete=models.SET_NULL, related_name='user')
    instructor = models.OneToOneField('InstructorInfo', null=True, blank=True, related_name='user')

    phone_number = PhoneNumberField(_('phone number'), null=True, blank=True)
    extra = models.TextField(null=True, blank=True)

    inactive = models.BooleanField(default=False)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        try:
            u = self.user
        except User.DoesNotExist:
            self.user = User.objects.create()
            self.user.save()

        if self.user and not self.user.username:
            import random
            import string
            self.user.username = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
            self.user.password = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(18))
            self.user.save()

        if not self.customer:
            c = CustomerInfo.objects.create()
            self.customer = c
        if not self.rider:
            r = RiderInfo.objects.create(customer=self.customer)
            self.rider = r
            self.rider.customer = self.customer
            self.rider.save()
        super(UserProfile, self).save()

    def get_next_participations(self):
        return self.get_participations().filter(state=0)[:3]

    def get_absolute_url(self):
        return reverse('view_user', args=(self.user.username,))

class RiderInfo(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        try:
            return unicode(self.user)
        except UserProfile.DoesNotExist:
            return 'N/A'
    levels = models.ManyToManyField(RiderLevel, related_name='+', blank=True)
    customer = models.ForeignKey(CustomerInfo)
    ticket_warning_limit = 1

class InstructorInfo(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return unicode(self.user)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = CustomerInfo
        fields = ['address']
