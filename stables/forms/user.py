from django import forms
from stables.models import RiderLevel
from stables.models import CustomerInfo
from stables.models import RiderInfo
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from stables.models import UserProfile
from stables.models import InstructorInfo

class UserProfileAddForm(forms.Form):
  first_name = forms.CharField(label=_('first name').capitalize(), max_length=500, required=True)
  last_name = forms.CharField(label=_('last name').capitalize(), max_length=500, required=True)
  phone_number = forms.CharField(label=_('phone number').capitalize(), max_length=500, required=False)
  email = forms.EmailField(label=_('email address').capitalize(), required=False)
  levels = forms.ModelMultipleChoiceField(label=_('levels').capitalize(), queryset=RiderLevel.objects.all(), required=False)

  def save(self, force_insert=False, force_update=False, commit=True):
    import random
    import string
    username = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    password = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(18))
    user = User.objects.create_user(username, self.cleaned_data['email'], password)
    user.first_name = self.cleaned_data['first_name']
    user.last_name = self.cleaned_data['last_name']
    user.save()

    #instance = super(UserProfileAdminAddForm, self).save(commit=False)
    instance = user.get_profile()

    if not instance.customer:
      c = CustomerInfo.objects.create()
      instance.customer = c
    if 'address' in self.cleaned_data and self.cleaned_data['address']:
      instance.customer.address = self.cleaned_data['address']

    if not instance.rider:
      r = RiderInfo.objects.create(customer=c)
      instance.rider = r
      instance.rider.customer = instance.customer
    if self.cleaned_data['levels']:
      instance.rider.levels = self.cleaned_data['levels']
    instance.phone_number = self.cleaned_data['phone_number']

    instance.save()
    instance.customer.save()
    instance.rider.customer = instance.customer
    instance.rider.save()
    return instance

  def save_m2m(self, *args, **kwargs):
      pass

class UserProfileForm(forms.ModelForm):
  first_name = forms.CharField(label=_('first name').capitalize(), max_length=500, required=True)
  last_name = forms.CharField(label=_('last name').capitalize(), max_length=500, required=True)
  levels = forms.ModelMultipleChoiceField(label=_('levels').capitalize(), queryset=RiderLevel.objects.all(), required=False)
  rider_customer = forms.ModelChoiceField(queryset=CustomerInfo.objects.all().prefetch_related('user__user'), required=True, label=_('Customer'))
  is_instructor = forms.BooleanField(label=_('instructor'), required=False)
  #address = forms.CharField(max_length=500, widget=forms.Textarea, required=False)

  def __init__(self, *args, **kwargs):
    super(UserProfileForm, self).__init__(*args, **kwargs)
    instance = kwargs.pop('instance', None)
    self.fields['levels'].initial=[x.id for x in instance.rider.levels.all()]
    self.fields['rider_customer'].initial=instance.rider.customer
    self.fields['phone_number'].initial=instance.phone_number
    self.fields['first_name'].initial=instance.user.first_name
    self.fields['last_name'].initial=instance.user.last_name
    self.fields['is_instructor'].initial=instance.instructor != None

  class Meta:
    model = UserProfile
    exclude = ('instructor', 'user', 'rider', 'customer')

  def save(self, force_insert=False, force_update=False, commit=True):
    instance = super(UserProfileForm, self).save(commit)
    instance.user.first_name = self.cleaned_data['first_name']
    instance.user.last_name = self.cleaned_data['last_name']
    instance.user.save()
    if self.cleaned_data['levels']:
      instance.rider.levels = self.cleaned_data['levels']
    if self.cleaned_data['rider_customer']:
      instance.rider.customer = self.cleaned_data['rider_customer']
    if self.cleaned_data['is_instructor'] and instance.instructor == None:
      instance.instructor = InstructorInfo.objects.create()
    if not self.cleaned_data['is_instructor'] and instance.instructor != None:
      instance.instructor.delete()
      instance.instructor = None
    instance.rider.save()
    instance.save()
    return instance
