from models import HorseForm, Horse, Course, Participation, PARTICIPATION_STATES
from models import Enroll
from models import UserProfile
from models import Transaction
from schedule.models import Occurrence
from django.shortcuts import render_to_response, redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
import datetime
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
import models as enum
import dateutil.parser

def render_response(req, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(req)
    return render_to_response(*args, **kwargs)

@require_POST
def confirm(request, action):
    context = dict(request.POST)
    del context[u'csrfmiddlewaretoken']
    return render(request, 'stables/confirm.html', { 'action': action, 'title': request.GET['title'],'back': request.META['HTTP_REFERER'], 'context': context })

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
    courses = Course.objects.exclude(end__lte=datetime.date.today())
    occs = {}
    for c in courses:
      for o in c.get_occurrences(delta=datetime.timedelta(days=6), start=datetime.date.today()):
        if not occs.has_key(o.start.hour):
          occs[o.start.hour] = {}
          for i in range(0,7):
            occs[o.start.hour][i] = []
        full = _("Space")
        if c.is_full(o):
          full = _("Full")
        occs[o.start.hour][o.start.weekday()].append((c, full))
    week = {}
    today = datetime.date.today()
    while today < datetime.date.today()+datetime.timedelta(days=7):
      week[today.weekday()] = (today, today.strftime('%a'))
      today = today+datetime.timedelta(days=1)
    return render_response(request, 'stables/courselist.html',
            { 'courses': courses, 'occurrences': occs, 'week': week })

def view_course(request, course_id):
    course = Course.objects.get(pk=course_id)
    occurrences = course.get_occurrences(start=datetime.date.today())
    return render_response(request, 'stables/course.html',
            { 'course': course, 'occurrences': occurrences })

def get_user_or_404(request, username, perm):
    if username and perm:
        return User.objects.filter(username=username)[0].get_profile()
    elif username != request.user.username:
        raise Http404
    return request.user.get_profile()

def attend_course(request, course_id):
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    course = get_object_or_404(Course, pk=course_id)
    occurrence = course.get_occurrence(start=dateutil.parser.parse(request.POST.get('start'))) #, end=request.POST.get('end')))
    course.attend(user, occurrence)
    return redirect('stables.views.view_course', course_id=int(course_id))

def cancel_participation(request, course_id):
    # Only user that has right to change permission
    user = get_user_or_404(request, request.POST.get('username'), request.user.has_perm('stables.change_participation'))
    pid = int(request.POST.get('participation_id'))
    if pid > 0:
        participation = get_object_or_404(Participation, pk=pid)
        participation.cancel()
    else:
        course = get_object_or_404(Course, pk=course_id)
        occurrence = course.get_occurrence(start=dateutil.parser.parse(request.POST.get('start'))) #, end=request.POST.get('end')))
        participation = course.create_participation(user, occurrence, enum.CANCELED)
    return redirect('stables.views.view_course', course_id=int(course_id))

def view_account(request):
    user = request.user.get_profile()
    return render(request, 'stables/account.html', { 'user': user })

def view_rider(request, username):
    rider = User.objects.filter(username=username)[0].get_profile()
    saldo = None
    if rider.customer and (request.user.has_perm('stables.can_view_saldo') or rider.customer.userprofile.user == request.user):
        saldo = rider.customer.saldo()
    return render_response(request, 'stables/rider.html', { 'rider': rider, 'saldo': saldo })

def view_customer(request, username):
    user = User.objects.filter(username=username)[0]
    customer = user.get_profile().customer
    if not customer:
        raise Http404
    if user != request.user and not request.user.has_perm('stables.view_transaction'):
        raise Http404
    trans = Transaction.objects.filter(active=True, customer=customer).order_by('-created_on')
    saldo = customer.saldo()
    return render_response(request, 'stables/customer.html', { 'customer': customer, 'transactions': trans, 'saldo': saldo })

import dateutil.parser
@permission_required('stables.change_participation')
def modify_participations(request, course_id, occurrence_start):
    course = get_object_or_404(Course, pk=course_id)
    occurrence = None
    participations = None
    users = UserProfile.objects.filter(rider__isnull=False)
    if occurrence_start:
        occurrence = course.get_occurrence(start=dateutil.parser.parse(occurrence_start))
        attnd = course.full_rider(occurrence, nolimit=True, include_statenames=True)
    return render(request, 'stables/participations.html', { 'course': course, 'occurrence': occurrence, 'participations': attnd, 'users': set(users) - set([k for k,v in attnd]) })

from models import admin, RiderInfo
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

@staff_member_required
def update_rider_levels(request):
  if request.method == 'POST':
    ids = request.POST.getlist('id')
    form = admin.RiderLevelForm(request.POST)
    if form.is_valid():
      for r in UserProfile.objects.filter(id__in=ids):
        if not r.rider:
          rider = RiderInfo.objects.create(customer=r.customer)
	  rider.levels = form.cleaned_data['levels']
	  r.rider = rider
	  r.save()
	else:
	  r.rider.levels = form.cleaned_data['levels']
        r.rider.save()
      return HttpResponseRedirect('/admin/stables/riderinfo')
  else:
    ids = request.GET.get('ids').split(',')
    form = admin.RiderLevelForm()
  return render(request, 'stables/riderlevels.html', { 'form': form, 'act': reverse('stables.views.update_rider_levels'), 'riders': ids })
