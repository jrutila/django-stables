from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic import FormView
from django.views.generic import DetailView
from stables.models import Course
from stables.forms import CourseForm
from stables.forms import AddEventForm
from datetime import *

class ViewCourse(DetailView):
    model = Course
    template_name = 'stables/course/course.html'

    def get_context_data(self, **kwargs):
        context = super(ViewCourse, self).get_context_data(**kwargs)
        context['occurrences'] = context['object'].get_occurrences(start=date.today()-timedelta(days=7))
        return context

class CourseCreate(CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'stables/course/course_form.html'

    def get_form(self, form_class):
      form = super(CourseCreate, self).get_form(form_class)
      form.user = self.request.user
      return form

class CourseUpdate(UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'stables/course/course_form.html'

    def get_form(self, form_class):
      form = super(CourseUpdate, self).get_form(form_class)
      form.user = self.request.user
      return form

class CourseAddEvent(FormView):
    template_name = 'stables/course/add_event.html'
    form_class = AddEventForm

    def post(self, request, *args, **kwargs):
        self.request = request
        self.course = Course.objects.get(**kwargs)
        self.success_url = self.course.get_absolute_url()
        return super(CourseAddEvent, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        form.request = self.request
        form.course = self.course
        form.save_event()
        return super(CourseAddEvent, self).form_valid(form)
