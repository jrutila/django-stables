from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse

from stables.models import Accident
from stables.models import Participation
from stables.models import InstructorParticipation
from stables.forms import AccidentForm

class CreateAccident(CreateView):
    model = Accident
    form_class = AccidentForm
    template_name = 'stables/course/course_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.participation = Participation.objects.get(pk=request.GET.get('participation_id'))
        self.success_url = self.participation.get_absolute_url()
        return super(CreateAccident, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(CreateAccident, self).get_initial()
        initial = initial.copy()
        if self.participation:
            initial['at'] = self.participation.start
            initial['horse'] = self.participation.horse
            initial['rider'] = self.participation.participant.rider
            ins = list(InstructorParticipation.objects.filter(
                start=self.participation.start,
                end=self.participation.end,
                event=self.participation.event
                )[:1])
            if ins:
                initial['instructor'] = ins[0].instructor.instructor
        return initial

    def get_form(self, form_class):
        form = super(CreateView, self).get_form(form_class)
        form.user = self.request.user
        return form
