from stables.models import Horse, UserProfile, RiderInfo, CustomerInfo, RiderLevel
from stables.models import CustomerForm, CourseForm
from stables.models import Course, Participation, Enroll
from stables.models import Transaction, Ticket, ParticipationTransactionActivator, CourseTransactionActivator, CourseParticipationActivator, TicketType
from stables.models import RiderLevel
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
import reversion

#class HorseAdmin(reversion.VersionAdmin):
    #pass
class CourseAdmin(admin.ModelAdmin):
    form =  CourseForm

class ParticipationAdmin(reversion.VersionAdmin):
    pass

class CustomerInfoAdmin(admin.ModelAdmin):
    model = CustomerInfo
    form = CustomerForm

class RiderInfoInline(admin.StackedInline):
    model = RiderInfo

class UserProfileAdminForm(forms.ModelForm):
  first_name = forms.CharField(max_length=500, required=True)
  last_name = forms.CharField(max_length=500, required=True)
  levels = forms.ModelMultipleChoiceField(queryset=RiderLevel.objects.all(), required=False)
  rider_customer = forms.ModelChoiceField(queryset=CustomerInfo.objects.all(), required=True, label=_('Customer'))
  #address = forms.CharField(max_length=500, widget=forms.Textarea, required=False)

  def __init__(self, *args, **kwargs):
    super(UserProfileAdminForm, self).__init__(*args, **kwargs)
    instance = kwargs.pop('instance', None)
    self.fields['levels'].initial=[x.id for x in instance.rider.levels.all()]
    self.fields['rider_customer'].initial=instance.rider.customer
    self.fields['phone_number'].initial=instance.phone_number
    self.fields['first_name'].initial=instance.user.first_name
    self.fields['last_name'].initial=instance.user.last_name

  class Meta:
    model = UserProfile

  def save(self, force_insert=False, force_update=False, commit=True):
    instance = super(UserProfileAdminForm, self).save(commit)
    instance.user.first_name = self.cleaned_data['first_name']
    instance.user.last_name = self.cleaned_data['last_name']
    instance.user.save()
    if self.cleaned_data['levels']:
      instance.rider.levels = self.cleaned_data['levels']
    if self.cleaned_data['rider_customer']:
      instance.rider.customer = self.cleaned_data['rider_customer']
    instance.rider.save()
    return instance

class UserProfileAdminAddForm(forms.ModelForm):
  first_name = forms.CharField(max_length=500, required=True)
  last_name = forms.CharField(max_length=500, required=True)
  phone_number = forms.CharField(max_length=500, required=False)
  email = forms.EmailField(required=False)
  levels = forms.ModelMultipleChoiceField(queryset=RiderLevel.objects.all(), required=False)

  class Meta:
    model = UserProfile

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

class UserProfileAdmin(admin.ModelAdmin):
  form = UserProfileAdminForm
  actions = ['update_riderlevels']
  search_fields = ['user__first_name', 'user__last_name', 'user__username']

  def change_view(self, request, form_url='', extra_context=None):
    self.form = UserProfileAdminForm
    self.exclude = ['rider', 'customer', 'user']
    return super(UserProfileAdmin, self).change_view(request, form_url, extra_context)

  def add_view(self, request, form_url='', extra_context=None):
    self.form = UserProfileAdminAddForm
    self.exclude = ['rider', 'customer', 'user']
    return super(UserProfileAdmin, self).add_view(request, form_url, extra_context)

  def update_riderlevels(self, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect(reverse('stables.views.update_rider_levels')+'?ids='+','.join(selected))

#admin.site.register(Horse, HorseAdmin)
admin.site.register(Horse)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(RiderInfo)
admin.site.register(CustomerInfo, CustomerInfoAdmin)
admin.site.register(Participation, ParticipationAdmin)
admin.site.register(RiderLevel)
admin.site.register(Enroll)
admin.site.register(Ticket)
admin.site.register(TicketType)
admin.site.register(Transaction)
admin.site.register(Course, CourseAdmin)
admin.site.register(ParticipationTransactionActivator)
admin.site.register(CourseTransactionActivator)
admin.site.register(CourseParticipationActivator)