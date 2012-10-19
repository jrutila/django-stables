from django.db import models
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from filer.fields.image import FilerImageField
from taggit.managers import TaggableManager
from django.core.exceptions import ValidationError

class Horse(models.Model):
    class Meta:
        app_label = 'stables'
    def __unicode__(self):
        return self.name
    name = models.CharField(_('name'), max_length=500)
    nickname = models.CharField(_('nickname'), max_length=500, null=True, blank=True)
    description = models.TextField(_('description'), max_length=2500, null=True, blank=True)
    breed = models.CharField(_('breed'), max_length=500, null=True, blank=True)
    withers = models.IntegerField(_('withers'), null=True, blank=True)
    birthday = models.DateField(_('birthday'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=1, choices=(('G', _('Gelding')), ('M', _('Mare')), ('S', _('Stallion'))), null=True, blank=True)
    mugshot = FilerImageField(null=True, blank=True)
    tags = TaggableManager(_('tags'))
    #owner = models.ForeignKey(Owner)
    last_usage_date = models.DateField(_('last usage date'), null=True, blank=True)

    @models.permalink
    def get_absolute_url(self):
        return ('stables.views.view_horse', (), { 'horse_id': self.id })

    def clean_fields(self, *args, **kwargs):
      from stables.models.participations import Participation
      if self.last_usage_date and Participation.objects.filter(horse=self, start__gt=self.last_usage_date):
        raise ValidationError({'last_usage_date': [_("Last usage date can't be before last participation")]})

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

