from django import forms
from stables.models import RiderLevel
from stables.models import CustomerInfo
from stables.models import RiderInfo
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from stables.models import UserProfile
from stables.models import InstructorInfo

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import HTML
from crispy_forms.layout import Layout, Fieldset, ButtonHolder

from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

class UserFormHelper(FormHelper):
    form_class = 'blueForms'
    form_method = 'post'

class UserProfileForm(forms.ModelForm):
  first_name = forms.CharField(label=_('first name').capitalize(), max_length=500, required=True)
  last_name = forms.CharField(label=_('last name').capitalize(), max_length=500, required=True)
  levels = forms.ModelMultipleChoiceField(label=_('levels').capitalize(), queryset=RiderLevel.objects.all(), required=False)
  rider_customer = forms.ModelChoiceField(queryset=CustomerInfo.objects.all().prefetch_related('user__user'), required=False, label=_('Customer'), help_text=_('If you are adding new rider, you can leave this empty.'))
  is_instructor = forms.BooleanField(label=_('instructor'), required=False)
  email = forms.EmailField(label=_('email address').capitalize(), required=False)
  address = forms.CharField(max_length=500, widget=forms.Textarea, required=False)

  inactive = forms.BooleanField(label=_('inactive'), required=False, help_text=_('Inactive rider is not shown in any lists. If you mark the rider as inactive you cannot edit it anymore!'))

  def __init__(self, *args, **kwargs):
    super(UserProfileForm, self).__init__(*args, **kwargs)
    instance = kwargs.pop('instance', None)
    if instance:
        self.fields['levels'].initial=[x.id for x in instance.rider.levels.all()]
        self.fields['rider_customer'].initial=instance.rider.customer
        self.fields['rider_customer'].required=True
        self.fields['phone_number'].initial=instance.phone_number
        self.fields['first_name'].initial=instance.user.first_name
        self.fields['last_name'].initial=instance.user.last_name
        self.fields['is_instructor'].initial=instance.instructor != None
        self.fields['email'].initial=instance.user.email
        self.fields['address'].initial=instance.customer.address

    self.helper = UserFormHelper()
    self.helper.layout = Layout(
            Fieldset(
              _('Basic information'),
              'first_name','last_name', 'email', 'phone_number'
              ),
            Fieldset(
              _('Levels '),
              'levels',
              ),
            Fieldset(
              _('Extra'),
              'is_instructor',
              'rider_customer',
              'address',
              'extra',
              ),
            ButtonHolder(
              Submit('submit', 'Submit')
              )
          )

    if instance:
        self.helper.layout[2].append('inactive')

  class Meta:
    model = UserProfile
    exclude = ('instructor', 'user', 'rider', 'customer')

  def clean_first_name(self):
      return " ".join(self.cleaned_data['first_name'].split()).title()
  def clean_last_name(self):
      return " ".join(self.cleaned_data['last_name'].split()).title()

  def clean(self):
      data = super(forms.ModelForm, self).clean()
      user = None
      if self.instance.id:
          return data
      try:
          if 'first_name' in self.cleaned_data and 'last_name' in self.cleaned_data:
              user = UserProfile.objects.get(
                  user__first_name=self.cleaned_data['first_name'],
                  user__last_name=self.cleaned_data['last_name']
                  )
      except UserProfile.DoesNotExist:
          return data
      if user:
          raise ValidationError(mark_safe(_("Existing user %s! Change first and last names") % ("<a href='%s'>%s</a>" % (user.get_absolute_url(), unicode(user)))))
      return data

  def save(self, force_insert=False, force_update=False, commit=True):
    instance = super(UserProfileForm, self).save(False)
    if not hasattr(instance, 'user'):
        import random
        import string
        username = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(18))
        user = User.objects.create_user(username, self.cleaned_data['email'], password)
        instance.user = user
    if not instance.customer:
      c = CustomerInfo.objects.create()
      instance.customer = c
    if not instance.rider:
      r = RiderInfo.objects.create(customer=instance.customer)
      instance.rider = r
      instance.rider.customer = instance.customer
    instance.user.first_name = self.cleaned_data['first_name']
    instance.user.last_name = self.cleaned_data['last_name']
    instance.user.email = self.cleaned_data['email']
    instance.user.save()
    instance.customer.address = self.cleaned_data['address']
    instance.customer.save()
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
