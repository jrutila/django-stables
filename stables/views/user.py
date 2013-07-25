from django.views.generic.edit import FormView
from stables.forms import UserProfileAddForm
from django.http import HttpResponse

class AddUser(FormView):
    template_name = 'stables/user/add_user.html'
    form_class = UserProfileAddForm

    def form_valid(self, form):
        form.save(commit = True)
        return HttpResponse('<script type="text/javascript">window.close()</script>Close this window.')

    def get_context_data(self, **kwargs):
        if self.request.GET.get('orig'):
            orig = self.request.GET.get('orig').split()
            form = kwargs['form']
            ff = ['first_name', 'last_name']
            for i in range(0, len(orig)):
                form.fields[ff[i]].initial = orig[i]
        return super(AddUser, self).get_context_data(**kwargs)

"""
    @method_decorator(permission_required('auth.add_user'))
    def dispatch(self, *args, **kwargs):
        return super(AddUser, self).dispatch(*args, **kwargs)
"""
