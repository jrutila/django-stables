from django import forms
from user import RiderLevel, RiderInfo

class RiderLevelForm(forms.ModelForm):
  class Meta:
    model = RiderInfo 
    exclude = ['customer']
  levels = forms.ModelMultipleChoiceField(queryset=RiderLevel.objects.all(), required=False)
