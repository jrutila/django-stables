from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic import FormView
from django.views.generic import DetailView
from django.views.generic import ListView

from stables.models import Course
from stables.forms import CourseForm
from stables.forms import AddEventForm
from stables.forms import ChangeEventForm
from datetime import *
import dateutil.parser

class ListCourse(ListView):
    model = Course
    template_name = 'stables/course/list.html'
    queryset = Course.objects.all().prefetch_related('events')

    def get_context_data(self, **kwargs):
        context = super(ListCourse, self).get_context_data(**kwargs)
        newlist = []
        for c in context['course_list']:
            next_occ = c.get_course_time_info()
            c.next_occ = None
            if next_occ:
                c.next_occ = next_occ
            newlist.append(c)
        context['course_list'] = sorted(newlist, key=lambda x: x.next_occ['start'].weekday if x.next_occ else None )
        return context

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
    template_name = 'stables/generic_form.html'

    def get_form(self, form_class):
      form = super(CourseCreate, self).get_form(form_class)
      form.user = self.request.user
      return form

class CourseUpdate(UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'stables/generic_form.html'

    def get_form(self, form_class):
      form = super(CourseUpdate, self).get_form(form_class)
      form.user = self.request.user
      return form

class CourseAddEvent(FormView):
    template_name = 'stables/generic_form.html'
    form_class = AddEventForm

    def dispatch(self, request, *args, **kwargs):
        self.course = Course.objects.get(**kwargs)
        self.success_url = self.course.get_absolute_url()
        return super(CourseAddEvent, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(FormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['course'] = self.course
        return kwargs

    def form_valid(self, form):
        form.save_event()
        return super(CourseAddEvent, self).form_valid(form)

class CourseUpdateEvent(CourseAddEvent):
    form_class = ChangeEventForm

    def dispatch(self, request, *args, **kwargs):
        start = dateutil.parser.parse(kwargs.pop('start'))
        self.course = Course.objects.get(**kwargs)
        self.event = self.course.get_occurrence(start)
        return super(CourseUpdateEvent, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CourseUpdateEvent, self).get_form_kwargs()
        kwargs['event'] = self.event
        return kwargs
