from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic import DetailView
from django.views.generic import ListView

from stables.models import Horse
from stables.forms import HorseForm

class ViewHorse(DetailView):
    model = Horse
    template_name = 'stables/horse/horse.html'

class HorseList(ListView):
    model = Horse
    template_name = 'stables/horse/horselist.html'

class HorseCreate(CreateView):
    model = Horse
    form_class = HorseForm
    template_name = 'stables/course/course_form.html'

class HorseUpdate(UpdateView):
    model = Horse
    form_class = HorseForm
    template_name = 'stables/course/course_form.html'
