from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django import forms
from django.core.urlresolvers import reverse
import datetime

class UserManager(models.Manager):
    def participate(self, rider, occurrence):
        part = Participation()
        part.participant = rider
        part.event = occurrence.event
        part.start = occurrence.start
        part.end = occurrence.end
        part.save()

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
    user = models.OneToOneField(User)
    rider = models.OneToOneField('RiderInfo', null=True, blank=True, related_name='user', on_delete=models.SET_NULL)
    customer = models.OneToOneField('CustomerInfo', null=True, blank=True, on_delete=models.SET_NULL)
    instructor = models.OneToOneField('InstructorInfo', null=True, blank=True, related_name='user')

    phone_number = models.CharField(max_length=30, null=True, blank=True)

    def get_participations(self):
        from participations import Participation
        return Participation.objects.filter(participant=self).order_by('start')

    def get_next_participations(self):
        return self.get_participations().filter(state=0)[:3]

    def get_absolute_url(self):
        return reverse('view_user', args=(self.user.username,))

def create_user_profile(sender, instance, created, **kwargs):
    if created:
      userprofile = UserProfile.objects.create(user=instance)
      userprofile.customer = CustomerInfo.objects.create()
      userprofile.rider = RiderInfo.objects.create(customer=userprofile.customer)
      userprofile.rider.customer = userprofile.customer
      userprofile.save()

post_save.connect(create_user_profile, sender=User, dispatch_uid="users-profilecreation-signal")

class CustomerInfo(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        try:
            return self.user.__unicode__()
        except:
            return self.address
    address = models.CharField(max_length=500)
    ticket_warning_limit = 1

class RiderInfo(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return self.user.__unicode__()
    levels = models.ManyToManyField(RiderLevel, related_name='+', blank=True)
    customer = models.ForeignKey(CustomerInfo)
    ticket_warning_limit = 1

class InstructorInfo(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return self.user.__unicode__()

class CustomerForm(forms.ModelForm):
    class Meta:
        model = CustomerInfo
    address = forms.CharField(widget=forms.Textarea)
