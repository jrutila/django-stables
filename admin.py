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

import reversion

#class HorseAdmin(reversion.VersionAdmin):
    #pass
class CourseAdmin(admin.ModelAdmin):
    form =  CourseForm

class ParticipationAdminForm(forms.ModelForm):
    class Meta:
        model = Participation

    def save(self, force_insert=False, force_update=False, commit=True):
        instance = super(ParticipationAdminForm, self).save(commit=False)
        # When we change the state from admin, do not update the state ts
        instance.save(True)
        return instance

#class ParticipationAdmin(reversion.VersionAdmin):
    #form = ParticipationAdminForm

class CustomerInfoAdmin(admin.ModelAdmin):
    model = CustomerInfo
    form = CustomerForm

class RiderInfoInline(admin.StackedInline):
    model = RiderInfo

class UserProfileAdminForm(forms.ModelForm):
  # TODO: These could be fetched from RiderInfo and CustomerInfo
  levels = forms.ModelMultipleChoiceField(queryset=RiderLevel.objects.all(), required=False)
  #address = forms.CharField(max_length=500, widget=forms.Textarea, required=False)

  class Meta:
    model = UserProfile

  def save(self, force_insert=False, force_update=False, commit=True):
    instance = super(UserProfileAdminForm, self).save(commit)
    if self.cleaned_data['levels']:
      instance.rider.levels = self.cleaned_data['levels']
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
    if self.cleaned_data['levels']:
      instance.rider.levels = self.cleaned_data['levels']
    instance.phone_number = self.cleaned_data['phone_number']

    instance.save()
    instance.customer.save()
    instance.rider.save()
    return instance

  def save_m2m(self, *args, **kwargs):
      pass

class UserProfileAdmin(admin.ModelAdmin):
  form = UserProfileAdminForm
  #exclude = ['rider', 'customer']
  #inlines = [RiderInfoInline]
  #inline_type = 'tabular'
  #inlines = []
  actions = ['update_riderlevels']

  def change_view(self, request, form_url='', extra_context=None):
    self.form = UserProfileAdminForm
    import pdb; pdb.set_trace()
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
#admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(RiderInfo)
admin.site.register(CustomerInfo, CustomerInfoAdmin)
#admin.site.register(Participation, ParticipationAdmin)
admin.site.register(RiderLevel)
admin.site.register(Participation)
admin.site.register(Enroll)
admin.site.register(Ticket)
admin.site.register(TicketType)
admin.site.register(Transaction)
admin.site.register(Course, CourseAdmin)
admin.site.register(ParticipationTransactionActivator)
admin.site.register(CourseTransactionActivator)
admin.site.register(CourseParticipationActivator)
