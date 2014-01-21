import reporting
from stables.models import Participation, InstructorParticipation
from stables.models import Transaction
from stables.models import Accident
from stables.models import ATTENDING
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from django.contrib.admin import RelatedFieldListFilter, DateFieldListFilter
from django.contrib.admin.util import get_model_from_relation
from django.db import models

from stables.forms.reports import DateFilterForm

import reportengine

from collections import defaultdict
from decimal import Decimal

def amountval_factory():
    return { 'amount': 0, 'value': Decimal('0.00') }

class FinanceReport(reportengine.Report):
    verbose_name = 'Finance report'
    slug = 'finance-report'
    namespace = 'stables'
    labels = ('horse', 'amount', 'value')

    def get_filter_form(self, data):
        form = DateFilterForm(data=data)
        return form

    def get_rows(self, filter={}, order_by=None):
        parts = Participation.objects.filter(state=ATTENDING, start__gte=filter['start'], end__lte=filter['end'])
        trans = Transaction.objects.filter(object_id__in=[ p.id for p in parts ])
        horses = defaultdict(amountval_factory)
        #{ 'amount': 0, 'value': Decimal('0.00')})
        rows = []
        for t in trans:
            if t.source.horse:
                horses[t.source.horse.name]['amount'] = horses[t.source.horse.name]['amount'] + 1
        for h,av in horses.items():
            rows.append([h, av.values()[0], av.values()[1]])
        return rows,(("total", len(rows)),)

reportengine.register(FinanceReport)


class MultipleRelatedFieldListFilter(RelatedFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(MultipleRelatedFieldListFilter, self).__init__(field,request,params,model,model_admin,field_path)
        other_model = get_model_from_relation(field)
        rel_name = other_model._meta.pk.name
        self.lookup_kwarg = '%s__%s__in' % (field_path, rel_name)
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)

    def choices(self, cl):
        from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE

        all_selected = self.lookup_val is None and not self.lookup_val_isnull
        yield {
          'selected': all_selected,
          'query_string': cl.get_query_string({},
              [self.lookup_kwarg, self.lookup_kwarg_isnull]),
          'display': _('All'),
          }
 
        if self.lookup_val:
            lookups = [ int(x) for x in self.lookup_val.split(',')]
        elif all_selected:
            lookups = [ x for x,y in self.lookup_choices ]
        else:
            lookups = []

        for pk_val, val in self.lookup_choices:
            selected = pk_val in lookups
            if selected:
              final_lo = [v for v in lookups if v != pk_val]
            else:
              final_lo = lookups + [pk_val]
            yield {
                'selected': selected,
                'query_string': cl.get_query_string({
                  self.lookup_kwarg: ','.join([str(x) for x in final_lo]),
                  }, [self.lookup_kwarg_isnull]),
                'display': val,
                }
        if (isinstance(self.field, models.related.RelatedObject)
                and self.field.field.null or hasattr(self.field, 'rel')
                    and self.field.null):
            yield {
                'selected': bool(self.lookup_val_isnull),
                'query_string': cl.get_query_string({
                    self.lookup_kwarg_isnull: 'True',
                }, [self.lookup_kwarg]),
                'display': EMPTY_CHANGELIST_VALUE,
            }

from django.utils import timezone
import datetime

class HorseReportDateFieldListFilter(DateFieldListFilter):
    template = 'stables/horsereport/filter.html'
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(HorseReportDateFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        if self.lookup_kwarg_until in self.used_parameters and not ':' in self.used_parameters[self.lookup_kwarg_until]:
            val = self.used_parameters[self.lookup_kwarg_until]
            val = datetime.datetime.strptime(val, '%Y-%m-%d') + datetime.timedelta(days=1)
            self.used_parameters[self.lookup_kwarg_until] = str(val)
        if self.lookup_kwarg_since in self.used_parameters and not ':' in self.used_parameters[self.lookup_kwarg_since]:
            val = self.used_parameters[self.lookup_kwarg_since]
            val = datetime.datetime.strptime(val, '%Y-%m-%d')
            self.used_parameters[self.lookup_kwarg_since] = str(val)
        now = timezone.now()     
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if now.tzinfo is not None:
            current_tz = timezone.get_current_timezone()
            now = now.astimezone(current_tz)
            if hasattr(current_tz, 'normalize'):
                # available for pytz time zones
                now = current_tz.normalize(now)
        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField 
            today = now.date()

        since = (datetime.datetime.strptime(self.used_parameters[self.lookup_kwarg_since], '%Y-%m-%d %H:%M:%S')).strftime('%Y-%m-%d') if self.lookup_kwarg_since in self.used_parameters else ''
        until = (datetime.datetime.strptime(self.used_parameters[self.lookup_kwarg_until], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1)).strftime('%Y-%m-%d') if self.lookup_kwarg_until in self.used_parameters else ''

        self.links = (
            ('custom', {
                self.lookup_kwarg_since: since,
                self.lookup_kwarg_until: until
              }),
            (_('This week'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=today.weekday())),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=7-today.weekday()))
              }),
            (_('Last week'), {
                self.lookup_kwarg_since: str(today - datetime.timedelta(days=7+today.weekday())),
                self.lookup_kwarg_until: str(today - datetime.timedelta(days=today.weekday()))
              }),
            (_('This month'), {
                self.lookup_kwarg_since: str(today.replace(day=1)),
                self.lookup_kwarg_until: str(today + datetime.timedelta(days=1)),
            }),
            (_('Last month'), {
                self.lookup_kwarg_since: str((today - datetime.timedelta(weeks=4)).replace(day=1)),
                self.lookup_kwarg_until: str(today.replace(day=1) - datetime.timedelta(days=1)),
            }),

            )
 

class HorseReport(reporting.Report):
  """Horse participation report"""
  model = Participation
  verbose_name = _("Horse report")

  aggregate = [
      ('id', Count, 'Total'),
      ]

  annotate = [
      ('id', Count, 'Total'),
      ]

  group_by = [
      ('horse', ('horse__name',)),
      ]

  list_filter = [
      ('start', HorseReportDateFieldListFilter),
      ('horse', MultipleRelatedFieldListFilter)
      ]

  def get_root_query_set(self, request):
      return self.model.objects.filter(state=ATTENDING)

reporting.register('horse', HorseReport)

class InstructorReport(reporting.Report):
  """Instructor participation report"""
  model = InstructorParticipation
  verbose_name = _("Instructor report")

  group_by = [
      ('instructor', ('instructor__user__first_name',)),
      ]

  aggregate = [
      ('id', Count, 'Total'),
      ]

  annotate = [
      ('id', Count, 'Total'),
      ]

  list_filter = [
      ('start', HorseReportDateFieldListFilter),
      ]

reporting.register('instructor', InstructorReport)

class AccidentReport(reporting.Report):
  """Instructor participation report"""
  model = Accident
  verbose_name = _("Accident report")

  list_display = [ 'at', 'type', 'horse', 'rider' ]

  list_filter = [
      ('at', HorseReportDateFieldListFilter),
      ]

reporting.register('accident', AccidentReport)
