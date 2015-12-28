from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

# class HorseAdmin(reversion.VersionAdmin):
# pass
from stables.models.accident import AccidentType, Accident
from stables.models.common import TicketType
from stables.models.course import Course, Enroll
from stables.models.financial import ParticipationTransactionActivator, Ticket, Transaction
from stables.models.horse import Horse
from stables.models.participations import InstructorParticipation, Participation, CourseParticipationActivator
from stables.models.user import CustomerInfo, RiderInfo, CustomerForm, RiderLevel, UserProfile, InstructorInfo


class CourseAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Basic information'), {
            'fields': ('name', 'start', 'end', 'creator', 'created_on', 'max_participants', 'allowed_levels')
        }),
        (_('Payment information'), {
            'fields': ('default_participation_fee', 'course_fee', 'ticket_type')
        }),
        (_('Recurring information'), {
            'description': _('Do NOT input anything here if you have one time events.'),
            'fields': ('starttime', 'endtime')
        }),
        (_('Advanced'), {
            'fields': ('events',)
        }),
    )


class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'state', 'start', 'end', 'created_on')
    search_fields = ['participant__user__first_name', 'participant__user__last_name', ]


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
    # address = forms.CharField(max_length=500, widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(UserProfileAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.pop('instance', None)
        self.fields['levels'].initial = [x.id for x in instance.rider.levels.all()]
        self.fields['rider_customer'].initial = instance.rider.customer
        self.fields['phone_number'].initial = instance.phone_number
        self.fields['first_name'].initial = instance.user.first_name
        self.fields['last_name'].initial = instance.user.last_name
        self.fields['is_instructor'].initial = instance.instructor != None

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
        fields = ["first_name", "last_name", "phone_number", "email", "levels"]

    def save(self, force_insert=False, force_update=False, commit=True):
        import random
        import string
        username = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
        password = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(18))
        user = User.objects.create_user(username, self.cleaned_data['email'], password)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # instance = super(UserProfileAdminAddForm, self).save(commit=False)
        instance = user.userprofile

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
        return HttpResponseRedirect(reverse_lazy('stables.views.update_rider_levels') + '?ids=' + ','.join(selected))


class InstructorParticipationAdminForm(forms.ModelForm):
    class Meta:
        model = InstructorParticipation
        fields = ["instructor"]

    instructor = forms.ModelChoiceField(queryset=InstructorInfo.objects.all(), required=True, label=_('Instructor'))

    # def __init__(self, instance):
    # super(InstructorParticipationAdminForm, self).__init__(instance)
    # TODO: Fix!
    # self.initial['instructor'] = instance.instructor.instructor.pk

    def clean_instructor(self):
        return UserProfile.objects.get(instructor__id=self.data['instructor'])


class InstructorParticipationAdmin(admin.ModelAdmin):
    form = InstructorParticipationAdminForm
    list_display = ('instructor', 'event', 'start', 'end')


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'source', 'active')
    search_fields = ['customer__user__user__first_name', 'customer__user__user__last_name', ]
    ordering = ['-created_on']
    actions = ['remove_and_preserve_ticket']

    def queryset(self, request):
        qs = super(TransactionAdmin, self).queryset(request)
        failed = request.GET.get('e')
        ids = []
        if failed[:4] == "fail":
            amount = failed.split("-")
            if len(amount) > 1:
                amount = amount[1]
            else:
                amount = 10
            for tr in qs:
                if len(ids) >= amount:
                    break
                occ = tr.source.get_occurrence()
                if not occ:
                    ids.append(tr.id)
            qs = qs.filter(id__in=ids)
        return qs

    def remove_and_preserve_ticket(self, request, queryset):
        for tr in queryset:
            for t in tr.ticket_set.all():
                t.transaction = None
                t.save()
            part = tr.source
            part.delete()
            tr.delete()


class ParticipationTransactionActivatorAdminForm(forms.ModelForm):
    class Meta:
        model = ParticipationTransactionActivator
        fields = []
        widgets = {
            'participation': forms.TextInput()
        }


class ParticipationTransactionActivatorAdmin(admin.ModelAdmin):
    form = ParticipationTransactionActivatorAdminForm
    actions = ['force_activate']

    def force_activate(self, request, queryset):
        for pac in queryset:
            pac.activate()


class TicketAdminForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['transaction']

    transaction = forms.IntegerField(required=False)

    def clean(self):
        if self.data['transaction']:
            self.cleaned_data['transaction'] = Transaction.objects.get(id=int(self.data['transaction']))
        return self.cleaned_data


class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    actions = ['make_familyticket']
    search_fields = ("name",)

    def get_search_results(self, request, queryset, search_term):
        if search_term == '':
            queryset, use_distinct = super(TicketAdmin,self).get_search_results(request, queryset, search_term)
        else:
            users = UserProfile.objects.filter(Q(user__first_name__icontains=search_term) | Q(user__last_name__icontains=search_term))
            custid = [u.customer.id for u in users]
            rideid = [u.rider.id for u in users]
            queryset = queryset.filter(Q(owner_id__in=custid) | Q(owner_id__in=rideid))
            use_distinct = False
        return queryset, use_distinct

    def make_familyticket(self, request, queryset):
        for ticket in queryset:
            owner = ticket.owner
            if isinstance(owner, RiderInfo):
                ticket.owner = owner.customer
                ticket.save()


class EnrollAdmin(admin.ModelAdmin):
    search_fields = ['participant__user__first_name']


class AccidentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'at', 'horse')


# admin.site.register(Horse, HorseAdmin)
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
admin.site.register(CourseParticipationActivator)
