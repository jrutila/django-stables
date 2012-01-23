from stables.models import Horse, UserProfile, RiderInfo, CustomerInfo, RiderLevel
from stables.models import CustomerForm, CourseForm
from stables.models import Course, Participation, Enroll
from stables.models import Transaction, Ticket, ParticipationTransactionActivator, CourseTransactionActivator, CourseParticipationActivator, TicketType
from stables.models import RiderLevel
from django import forms
from django.contrib import admin
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
  address = forms.CharField(max_length=500, widget=forms.Textarea, required=False)

  class Meta:
    model = UserProfile

  def save(self, force_insert=False, force_update=False, commit=True):
    instance = super(UserProfileAdminForm, self).save(commit=False)
    if self.cleaned_data['address']:
      if not instance.customer:
        c = CustomerInfo.objects.create(address=self.cleaned_data['address'])
        instance.customer = c
      instance.customer.address = self.cleaned_data['address']
    if self.cleaned_data['levels']:
      if not instance.rider:
        r = RiderInfo.objects.create(customer=c)
        instance.rider = r
      instance.rider.levels = self.cleaned_data['levels']
    instance.save()
    instance.customer.save()
    instance.rider.save()
    return instance

class UserProfileAdmin(admin.ModelAdmin):
  form = UserProfileAdminForm
  #exclude = ['rider', 'customer']
  #inlines = [RiderInfoInline]
  #inline_type = 'tabular'
  #inlines = []
  actions = ['update_riderlevels']

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
