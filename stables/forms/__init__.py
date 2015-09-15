#from stables.forms.course import *
#from stables.forms.user import *
#from stables.forms.horse import *
#from stables.forms.financial import *
#from stables.forms.accident import *
from crispy_forms.helper import FormHelper


class GenericFormHelper(FormHelper):
    form_class = "blueForms"
    form_method = "post"