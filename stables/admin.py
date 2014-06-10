from stables.models import Horse, UserProfile, RiderInfo, CustomerInfo, RiderLevel, InstructorInfo
from stables.models import CustomerForm
from stables.forms import CourseForm
from stables.models import Course, Participation, Enroll, InstructorParticipation, EventMetaData
from stables.models import Transaction, Ticket, ParticipationTransactionActivator, CourseTransactionActivator, CourseParticipationActivator, TicketType
from stables.models import Accident, AccidentType
from stables.models import RiderLevel
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
import reversion

#class HorseAdmin(reversion.VersionAdmin):
    #pass

class CourseAdmin(admin.ModelAdmin):
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
  actions = ['update_riderlevels']
  search_fields = ['user__first_name', 'user__last_name', 'user__username']

  def update_riderlevels(self, request, queryset):
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect(reverse('stables.views.update_rider_levels')+'?ids='+','.join(selected))

class InstructorParticipationAdminForm(forms.ModelForm):
    class Meta:
        model = InstructorParticipation
    instructor = forms.ModelChoiceField(queryset=InstructorInfo.objects.all(), required=True, label=_('Instructor'))

    #def __init__(self, instance):
        #super(InstructorParticipationAdminForm, self).__init__(instance)
        # TODO: Fix!
        #self.initial['instructor'] = instance.instructor.instructor.pk

    def clean_instructor(self):
        return UserProfile.objects.get(instructor__id=self.data['instructor'])

class InstructorParticipationAdmin(admin.ModelAdmin):
  form = InstructorParticipationAdminForm
  list_display = ('instructor', 'event', 'start', 'end')

class TransactionAdmin(reversion.VersionAdmin):
  list_display = ('customer', 'amount', 'source', 'active')
  search_fields = ['customer__userprofile__user__first_name', 'customer__userprofile__user__last_name',]
  ordering = ['-created_on']

class ParticipationTransactionActivatorAdminForm(forms.ModelForm):
  class Meta:
    model = ParticipationTransactionActivator
    widgets = {
        'participation': forms.TextInput()
        }

class ParticipationTransactionActivatorAdmin(admin.ModelAdmin):
  form = ParticipationTransactionActivatorAdminForm
  actions = ['force_activate']

  def  force_activate(self, request, queryset):
      for pac in queryset:
          pac.activate()

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
  actions = ['make_familyticket']

  def queryset(self, request):
    qs = super(TicketAdmin, self).queryset(request)
    q = request.GET.get('q')
    if q:
      users = UserProfile.objects.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q))
      custid = [ u.customer.id for u in users ]
      rideid = [ u.rider.id for u in users ]
      qs = qs.filter(Q(owner_id__in=custid) | Q(owner_id__in=rideid))
    return qs

  def make_familyticket(self, request, queryset):
    for ticket in queryset:
      owner = ticket.owner
      if isinstance(owner, RiderInfo):
        ticket.owner = owner.customer
        ticket.save()

class EnrollAdmin(reversion.VersionAdmin):
  search_fields = ['participant__user__first_name']

class AccidentAdmin(reversion.VersionAdmin):
  list_display = ('__unicode__', 'at', 'horse')

#admin.site.register(Horse, HorseAdmin)
admin.site.register(Horse)
admin.site.register(Accident, AccidentAdmin)
admin.site.register(AccidentType)
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
admin.site.register(Course)
admin.site.register(ParticipationTransactionActivator, ParticipationTransactionActivatorAdmin)
admin.site.register(CourseTransactionActivator)
admin.site.register(CourseParticipationActivator)
admin.site.register(EventMetaData)
