from stables.models import Horse, UserProfile, RiderInfo, CustomerInfo, RiderLevel
from stables.models import CustomerForm, CourseForm
from stables.models import Course, Participation, Enroll
from stables.models import Transaction, Ticket, ParticipationTransactionActivator, CourseTransactionActivator
from django import forms
from django.contrib import admin

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

#class UserProfileAdmin(reversion.VersionAdmin):
    #inlines = []

#admin.site.register(Horse, HorseAdmin)
admin.site.register(Horse)
#admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserProfile)
admin.site.register(RiderInfo)
admin.site.register(CustomerInfo, CustomerInfoAdmin)
#admin.site.register(Participation, ParticipationAdmin)
admin.site.register(RiderLevel)
admin.site.register(Participation)
admin.site.register(Enroll)
admin.site.register(Ticket)
admin.site.register(Transaction)
admin.site.register(Course, CourseAdmin)
admin.site.register(ParticipationTransactionActivator)
admin.site.register(CourseTransactionActivator)
