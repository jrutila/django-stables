from crispy_forms.bootstrap import FormActions
from django import forms
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Field


from django.utils import formats
from stables.forms import GenericFormHelper
from stables.models.horse import Horse


class HorseForm(forms.ModelForm):
    class Meta:
        model = Horse
        fields = ['name', 'day_limit', 'last_usage_date']

    #last_usage_date = forms.DateField(input_formats=formats.get_format('DATE_INPUT_FORMATS'), required=False)

    def __init__(self, *args, **kwargs):
      super(HorseForm, self).__init__(*args, **kwargs)
      self.helper = GenericFormHelper()
      self.helper.layout = Layout(
            Fieldset(
              _('Basic information'), 
              'name', 'day_limit'
              ),
            Fieldset(
              _('Expire information'), 
              Field('last_usage_date'),
              ),
            FormActions(
              Submit('submit', 'Submit')
              )
          )
