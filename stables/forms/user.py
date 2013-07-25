from django import forms
from stables.models import RiderLevel
from stables.models import CustomerInfo
from stables.models import RiderInfo
from django.contrib.auth.models import User

class UserProfileAddForm(forms.Form):
  first_name = forms.CharField(max_length=500, required=True)
  last_name = forms.CharField(max_length=500, required=True)
  phone_number = forms.CharField(max_length=500, required=False)
  email = forms.EmailField(required=False)
  levels = forms.ModelMultipleChoiceField(queryset=RiderLevel.objects.all(), required=False)

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
