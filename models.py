from django.db import models
from django.contrib.auth.models import User
from schedule.models import Calendar
from django import forms
from django.template.defaultfilters import slugify

import logging

class HorseManager(models.Manager):
    def create_calendar(self, name):
        cal = Calendar()
        cal.name = name
        cal.slug = slugify(name)
        cal.save()
        return cal

class Horse(models.Model):
    def __unicode__(self):
        return self.name
    name = models.CharField(max_length=500)
    birthday = models.DateField()
    calendar = models.ForeignKey(Calendar)
    objects = HorseManager()

    @models.permalink
    def get_absolute_url(self):
        return ('stables.views.view_horse', (), { 'horse_id': self.id })

class HorseForm(forms.ModelForm):
    class Meta:
        model = Horse
        exclude = ('calendar',)

    def save(self):
        if not self.instance.id:
            logging.debug('Create calendar with name %s' % self.cleaned_data['name'])
            cal = Horse.objects.create_calendar(self.cleaned_data['name'])
            self.instance.calendar = cal
            horse = forms.ModelForm.save(self)
            cal.create_relation(horse, 'horse')
        if not horse:
            horse = forms.ModelForm.save(self)
        return horse

class Rider(User):
    pass

class Owner(User):
    horses = models.ManyToManyField(Horse)
