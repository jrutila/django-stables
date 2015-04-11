from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

class Horse(models.Model):
    class Meta:
        app_label = 'stables'
        ordering = ['name']
    def __unicode__(self):
        return self.name
    name = models.CharField(_('name'), max_length=500)
    last_usage_date = models.DateField(_('last usage date'), null=True, blank=True)
    day_limit = models.IntegerField(_('day limit'), null=True, blank=True,
        help_text=_('How many times the horse is allowed to ride in a day. Warning will be shown if this limit is topped.'))

    @models.permalink
    def get_absolute_url(self):
        return ('view_horse', (), { 'pk': self.id })

    def clean_fields(self, *args, **kwargs):
      from stables.models.participations import Participation
      if self.last_usage_date and Participation.objects.filter(horse=self, start__gt=self.last_usage_date):
        raise ValidationError({'last_usage_date': [_("Last usage date can't be before last participation")]})
