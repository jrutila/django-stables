from django import forms

from crispy_forms.helper import FormHelper

class FilterFormHelper(FormHelper):
    form_class = 'blueForms'
    form_method = 'post'

class DateFilterForm(forms.Form):
    start = forms.DateField()
    end = forms.DateField()
