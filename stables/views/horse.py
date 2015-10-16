from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.core.urlresolvers import reverse

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from stables.models.horse import Horse
from stables.forms.horse import HorseForm

class HorseEditorMixin(object):
    @method_decorator(permission_required('stables.change_horse'))
    def dispatch(self, request, *args, **kwargs):
        return super(HorseEditorMixin, self).dispatch(request, *args, **kwargs)

class ViewHorse(HorseEditorMixin, DetailView):
    model = Horse
    template_name = 'stables/horse/horse.html'

class HorseList(HorseEditorMixin, ListView):
    model = Horse
    template_name = 'stables/horse/horselist.html'

class HorseCreate(HorseEditorMixin, CreateView):
    model = Horse
    form_class = HorseForm
    template_name = 'stables/generic_form.html'
    def get_success_url(*args):
        return reverse('list_horse')

class HorseUpdate(HorseEditorMixin, UpdateView):
    model = Horse
    form_class = HorseForm
    template_name = 'stables/generic_form.html'
    def get_success_url(*args):
        return reverse('list_horse')
