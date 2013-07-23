from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from stables.models import Course
from stables.forms import CourseForm

class CourseCreate(CreateView):
    model = Course
    form_class = CourseForm

    def get_form(self, form_class):
      form = super(CourseCreate, self).get_form(form_class)
      form.user = self.request.user
      return form

class CourseUpdate(UpdateView):
    model = Course
    form_class = CourseForm

