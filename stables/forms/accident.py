from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout
from crispy_forms.layout import ButtonHolder

from stables.models import Accident

class AccidentForm(forms.ModelForm):
    class Meta:
        model = Accident

    def __init__(self, *args, **kwargs):
      super(AccidentForm, self).__init__(*args, **kwargs)
      self.helper = FormHelper()
      self.helper.layout = Layout(
            'type', 'at', 'rider', 'horse', 'instructor', 'description',
            ButtonHolder(
              Submit('submit', 'Submit')
              )
          )
