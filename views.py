from models import HorseForm, Horse, Course, Participation, PARTICIPATION_STATES
from django.shortcuts import render_to_response, redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
import datetime

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return render_to_response(*args, **kwargs)

def add_horse(request):
    if request.method == "POST":
        form = HorseForm(request.POST)
        if form.is_valid():
            horse = form.save()
            return redirect(horse)
    else:
        form = HorseForm()
    return render_response(request, 'stables/addhorse.html', { 'form': form })

def view_horse(request, horse_id):
    horse = Horse.objects.get(pk=horse_id)
    return render_response(request, 'stables/horse.html', { 'horse': horse })

def list_course(request):
    courses = Course.objects.filter(end__gt=datetime.date.today())
    return render_response(request, 'stables/courselist.html',
            { 'courses': courses })

def view_course(request, course_id):
    user = request.user.get_profile()
    course = Course.objects.get(pk=course_id)
    occurrences = course.get_occurrences()
    user_participations = Participation.objects.filter(participant=user)
    participations = [] 
    for o in occurrences:
        parti = { 'state': { '1': _('Not attending') }}
        for p in user_participations:
            if p.get_occurrence() == o:
                parti = p
                parti.state = PARTICIPATION_STATES[p.state]
        participations.append((o, parti))
    return render_response(request, 'stables/course.html',
            { 'course': course, 'occurrences': participations })

def attend_course(request, course_id):
    course = Course.objects.get(pk=course_id)
    occurrence = course.get_occurrences()[int(request.POST.get('occurrence_index'))]
    course.attend(request.user.get_profile(), occurrence)
    return redirect('stables.views.view_course', course_id=int(course_id))

def cancel_participation(request, course_id):
    participation = Participation.objects.get(pk=request.POST.get('participation_id'))
    participation.cancel()
    return redirect('stables.views.view_course', course_id=int(course_id))

def view_rider(request, username):
    rider = User.objects.filter(username=username)[0].get_profile()
    return render_response(request, 'stables/rider.html', { 'rider': rider })
