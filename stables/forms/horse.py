from django import forms
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Field

from stables.models import Horse

from django.utils import formats

class HorseFormHelper(FormHelper):
    form_class = 'blueForms'
    form_method = 'post'

class HorseForm(forms.ModelForm):
    class Meta:
        model = Horse

    last_usage_date = forms.DateField(input_formats=formats.get_format('DATE_INPUT_FORMATS'), required=False)

    def __init__(self, *args, **kwargs):
      super(HorseForm, self).__init__(*args, **kwargs)
      self.helper = HorseFormHelper()
      self.helper.layout = Layout(
            Fieldset(
              _('Basic information'), 
              'name' 
              ),
            Fieldset(
              _('Expire information'), 
              Field('last_usage_date'),
              ),
            ButtonHolder(
              Submit('submit', 'Submit')
              )
          )
