from django.db import models
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.urlresolvers import reverse

#--i18nfield begin

from django.conf import settings
from django import forms
import django
import json
from stables.models.horse import Horse
from stables.models.user import RiderInfo, InstructorInfo


class LocalizedText():
    def __init__(self, d=None):
        if not d:
            d = {}
            for l in settings.LANGUAGES:
                d[l[0]] = ""
        self.texts = d

    def __unicode__(self):
        lang = django.utils.translation.get_language()
        return self.texts.get(lang, self.texts.get(lang.split('-')[0]))

class LocalizedTextInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        super(LocalizedTextInput, self).__init__(*args, **kwargs)

    def render(self, name, value, *args, **kwargs):
        if not value:
            value=LocalizedText()
        value = json.dumps(value.texts)
        return super(LocalizedTextInput, self).render(name, value, *args, **kwargs)


class I18NCharField(models.CharField):
    description = _("Localizable String")

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        langs = len(settings.LANGUAGES)
        kwargs['max_length'] = langs*(kwargs['max_length']+10)
        kwargs['max_length'] = 1000
        super(models.CharField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        if isinstance(value, LocalizedText):
            return value
        if not value:
            return value
        return LocalizedText(eval(super(models.CharField, self).to_python(value)))

    def get_prep_value(self, value):
        if not value:
            return value
        if isinstance(value, LocalizedText):
            return unicode(value.texts)
        return value

    def formfield(self, **kwargs):
        ff = super(models.CharField, self).formfield(**kwargs)
        ff.widget = LocalizedTextInput()
        return ff

#--END

class AccidentType(models.Model):
    class Meta:
        app_label = "stables"

    def __unicode__(self):
        return unicode(self.name)

    name = I18NCharField(max_length=20)

class Accident(models.Model):
    class Meta:
        verbose_name = _('accident')
        verbose_name_plural = _('accidents')
        app_label = "stables"
        permissions = (
            ('view_accidents', "Can see detailed accident reports"),
        )

    def __unicode__(self):
        return unicode(self.rider)+" "+unicode(self.type)

    def get_absolute_url(self):
        return reverse('edit_accident', args=(self.pk,))

    type = models.ForeignKey(AccidentType)
    at = models.DateTimeField()
    rider = models.ForeignKey(RiderInfo)
    horse = models.ForeignKey(Horse)
    instructor = models.ForeignKey(InstructorInfo, null=True, blank=True)
    description = models.TextField()
