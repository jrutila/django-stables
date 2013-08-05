from django import forms
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout, Fieldset, ButtonHolder

from stables.models import Horse

class HorseFormHelper(FormHelper):
    form_class = 'blueForms'
    form_method = 'post'

class HorseForm(forms.ModelForm):
    class Meta:
        model = Horse

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
              'last_usage_date' 
              ),
            ButtonHolder(
              Submit('submit', 'Submit')
              )
          )
