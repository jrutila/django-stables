from django.db import models
from django import forms

class Horse(models.Model):
    def __unicode__(self):
        return self.name
    name = models.CharField(max_length=500)
    birthday = models.DateField()
    #owner = models.ForeignKey(Owner)

    @models.permalink
    def get_absolute_url(self):
        return ('stables.views.view_horse', (), { 'horse_id': self.id })

class HorseForm(forms.ModelForm):
    class Meta:
        model = Horse

    def save(self):
        if not self.instance.id:
            logging.debug('Create calendar with name %s' % self.cleaned_data['name'])
            horse = forms.ModelForm.save(self)
        if not horse:
            horse = forms.ModelForm.save(self)
        return horse

