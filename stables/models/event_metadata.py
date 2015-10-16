from stables.models import part_move

__author__ = 'jorutila'

from django.db.models import Q
from django.db import models
from schedule.models import Event
from django.utils.translation import ugettext, ugettext_lazy as _

class EventMetaDataManager(models.Manager):
    def get_metadatas(self, start, end):
        events = Event.objects.filter((Q(rule__frequency='WEEKLY') & (Q(end_recurring_period__gte=start) | Q(end_recurring_period__isnull=True))) | (Q(rule__isnull=True) & Q(start__gte=start) & Q(end__lte=end)) | (Q(occurrence__start__gte=start) & Q(occurrence__end__lte=end))).select_related('rule').prefetch_related('course_set')
        ret = {}
        for event in events:
            if event.course_set.count() == 0:
              continue
            for occ in event.get_occurrences(start, end):
                ret[occ] = (event.course_set.all()[0], list(EventMetaData.objects.filter(event=event, start=occ.start, end=occ.end)))

        return ret

    move = part_move

class EventMetaData(models.Model):
    class Meta:
        app_label = 'stables'
    objects = EventMetaDataManager()

    event = models.ForeignKey(Event)
    start = models.DateTimeField()
    end = models.DateTimeField()

    #max_participants = models.IntegerField(_('maximum participants'), blank=True, null=True) #, default=django_settings.get("default_max_participants", default=7))
    #default_participation_fee = CurrencyField(_('default participation fee'), blank=True, null=True)#, default=django_settings.get("default_participation_fee", default=0.00))
