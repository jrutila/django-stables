from crispy_forms.bootstrap import FormActions
from django import forms
from crispy_forms.layout import Submit
from crispy_forms.layout import Layout
from crispy_forms.layout import ButtonHolder
from stables.forms import GenericFormHelper
from stables.models.accident import Accident
from stables.models.user import RiderInfo


class AccidentForm(forms.ModelForm):
    class Meta:
        model = Accident
        exclude = []

    def __init__(self, *args, **kwargs):
        super(AccidentForm, self).__init__(*args, **kwargs)
        self.fields['rider'].queryset = RiderInfo.objects.all().prefetch_related('user__user')
        self.helper = GenericFormHelper()
        self.helper.layout = Layout(
            'type', 'at', 'rider', 'horse', 'instructor', 'description',
            FormActions(
                Submit('submit', 'Submit')
            )
        )
