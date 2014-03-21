from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

from stables.views.oldviews import *
from stables.views.course import *
from stables.views.user import *
from stables.views.participation import *
from stables.views.horse import *
from stables.views.financial import *
from stables.views.accident import *

