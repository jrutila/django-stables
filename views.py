from models import HorseForm, Horse
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext

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

