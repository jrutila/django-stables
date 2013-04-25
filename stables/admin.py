from stables.models import Horse, UserProfile, RiderInfo, CustomerInfo, RiderLevel, InstructorInfo
from stables.models import CustomerForm, CourseForm
from stables.models import Course, Participation, Enroll, InstructorParticipation
from stables.models import Transaction, Ticket, ParticipationTransactionActivator, CourseTransactionActivator, CourseParticipationActivator, TicketType
from stables.models import RiderLevel
from schedule.models import Event
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
    fieldsets = (
      (_('Basic information'), {
        'fields': ('name','start', 'end', 'creator', 'created_on', 'max_participants', 'allowed_levels' )
      }),
      (_('Payment information'), {
        'fields': ('default_participation_fee', 'course_fee', 'ticket_type' )
      }),
      (_('Recurring information'), {
        'description': _('Do NOT input anything here if you have one time events.'),
        'fields': ('starttime', 'endtime')
      }),
      (_('Advanced'), {
        'fields': ('events',)
      }),
    )

class ParticipationAdmin(reversion.VersionAdmin):
    list_display = ('participant', 'state', 'start', 'end', 'created_on')
    search_fields = ['participant__user__first_name', 'participant__user__last_name',]

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
  is_instructor = forms.BooleanField(required=False)
  #address = forms.CharField(max_length=500, widget=forms.Textarea, required=False)

  def __init__(self, *args, **kwargs):
    super(UserProfileAdminForm, self).__init__(*args, **kwargs)
    instance = kwargs.pop('instance', None)
    self.fields['levels'].initial=[x.id for x in instance.rider.levels.all()]
    self.fields['rider_customer'].initial=instance.rider.customer
    self.fields['phone_number'].initial=instance.phone_number
    self.fields['first_name'].initial=instance.user.first_name
    self.fields['last_name'].initial=instance.user.last_name
    self.fields['is_instructor'].initial=instance.instructor != None

  class Meta:
    model = UserProfile
    exclude = ('instructor',)

  def save(self, force_insert=False, force_update=False, commit=True):
    instance = super(UserProfileAdminForm, self).save(commit)
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

  def get_form(self, request, obj=None, **kwargs):
      self.exclude = ['rider', 'customer', 'user']
      if obj is None:
          self.form = UserProfileAdminAddForm
      else:
          self.form = UserProfileAdminForm
      return super(UserProfileAdmin, self).get_form(request, obj, **kwargs)

  def update_riderlevels(self, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect(reverse('stables.views.update_rider_levels')+'?ids='+','.join(selected))

class InstructorParticipationAdmin(admin.ModelAdmin):
  list_display = ('instructor', 'event', 'start', 'end')

class TransactionAdmin(reversion.VersionAdmin):
  list_display = ('customer', 'amount', 'source', 'active')
  search_fields = ['customer__userprofile__user__first_name', 'customer__userprofile__user__last_name',]
  ordering = ['-created_on']

class TicketAdminForm(forms.ModelForm):
  class Meta:
    model = Ticket
    #exclude = ['transaction' ]
  transaction = forms.IntegerField(required=False)

  def clean(self):
    if self.data['transaction']:
      self.cleaned_data['transaction'] = Transaction.objects.get(id=int(self.data['transaction']))
    return self.cleaned_data

class TicketAdmin(admin.ModelAdmin):
  form = TicketAdminForm

class EnrollAdmin(reversion.VersionAdmin):
  search_fields = ['participant__user__first_name']

#admin.site.register(Horse, HorseAdmin)
admin.site.register(Horse)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(RiderInfo)
admin.site.register(CustomerInfo, CustomerInfoAdmin)
admin.site.register(Participation, ParticipationAdmin)
admin.site.register(InstructorParticipation, InstructorParticipationAdmin)
admin.site.register(RiderLevel)
admin.site.register(Enroll, EnrollAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketType)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(ParticipationTransactionActivator)
admin.site.register(CourseTransactionActivator)
admin.site.register(CourseParticipationActivator)
