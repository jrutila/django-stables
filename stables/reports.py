from stables.models import Participation, InstructorParticipation
from stables.models import Transaction
from stables.models import Accident
from stables.models import ATTENDING, CANCELED, RESERVED, SKIPPED
from stables.forms.reports import DateFilterForm
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _, ugettext
from django.contrib.contenttypes.models import ContentType
import datetime
from collections import defaultdict
from decimal import Decimal
import reportengine

def amountval_factory():
    return { 'amount': 0, 'value': Decimal('0.00') }

def get_daterange(start, end):
    if start:
        start = datetime.datetime.combine(start, datetime.datetime.min.time())
    else:
        start = datetime.datetime.min
    if end:
        end = datetime.datetime.combine(end, datetime.datetime.max.time())
    else:
        end = datetime.datetime.max
    return start,end

class FinanceReport(reportengine.Report):
    namespace = 'stables'
    states = [ATTENDING]

    def get_filter_form(self, data):
        form = DateFilterForm(data=data)
        return form

    def get_value(self, trans):
        return eval("trans.source"+self.attr)

    def get_rows(self, filter={}, order_by=None):
        start, end = get_daterange(filter['start'], filter['end'])
        parts = Participation.objects.filter(start__gte=start, end__lte=end).filter(state__in=self.states).prefetch_related('participant')
        trans = Transaction.objects.filter(object_id__in=[ p.id for p in parts ], content_type=ContentType.objects.get_for_model(Participation)).prefetch_related('ticket_set', 'source__participant__user', 'source__event__course_set', 'source__horse')
        values = defaultdict(amountval_factory)
        rows = []
        for t in trans:
            value = self.get_value(t)
            if value:
                values[value.__unicode__()]['amount'] = values[value.__unicode__()]['amount'] + 1
                values[value.__unicode__()]['value'] = values[value.__unicode__()]['value'] + t.getIncomeValue()
        for h,av in values.items():
            rows.append([h, av.values()[0], av.values()[1]])
        return rows,(("total", len(rows)),)

class FakeTicket():
    def __init__(self, trans):
        self.method = trans.method
        if not self.method:
            self.method = ugettext("Cash")
    def __unicode__(self):
        return self.method

class PaymentTypeReport(FinanceReport):
    namespace = 'stables'
    slug = "payment-report"
    labels = ('payment type', 'amount', 'value')
    verbose_name = 'Payment type report'
    states = [ATTENDING, SKIPPED]

    def get_value(self, trans):
        tckts = trans.ticket_set.all()
        if (tckts.count() == 0):
            if trans.amount >= 0:
                return FakeTicket(trans)
            return None
        return tckts[0].type

class HorseFinanceReport(FinanceReport):
    labels = ('horse', 'amount', 'value')
    attr = '.horse'
    slug = 'horse-report'
    verbose_name = 'Horse report'

class CourseFinanceReport(FinanceReport):
    labels = ('course', 'amount', 'value')
    attr = '.event.course_set.all()[0]'
    slug = 'course-report'
    verbose_name = 'Course report'

    def get_value(self, trans):
        source = trans.source
        cs = source.event.course_set.all()
        if cs:
            return cs[0]
        return None

class RiderFinanceReport(FinanceReport):
    labels = ('rider', 'amount', 'value')
    attr = '.participant'
    slug = 'rider-report'
    verbose_name = 'Rider report'

reportengine.register(PaymentTypeReport)
reportengine.register(HorseFinanceReport)
reportengine.register(CourseFinanceReport)
reportengine.register(RiderFinanceReport)

class InstructorReport(reportengine.QuerySetReport):
    namespace = 'stables'
    slug = 'instructor-report'
    verbose_name = 'Instructor report'
    labels = ('instructor__user__first_name', 'amount')

    def get_filter_form(self, data):
        form = DateFilterForm(data=data)
        return form

    def get_queryset(self, filters, order_by, queryset=None):
        start, end = get_daterange(filters['start'], filters['end'])
        instr = InstructorParticipation.objects.filter(
                start__gte=start,
                end__lte=end).values('instructor').annotate(
                        amount=Count('instructor'))
        return instr

reportengine.register(InstructorReport)

class AccidentReport(reportengine.QuerySetReport):
    namespace = 'stables'
    slug = 'accident-report'
    verbose_name = 'Accident report'
    labels = (_('At'), _('Horse'), _('Rider name'), _('Type'))

    def get_filter_form(self, data):
        form = DateFilterForm(data=data)
        return form

    def get_queryset(self, filters, order_by, queryset=None):
        start, end = get_daterange(filters['start'], filters['end'])
        instr = Accident.objects.filter(
                at__gte=start,
                at__lte=end)
        return instr

    def get_rows(self,filters={},order_by=None):
        qs = self.get_queryset(filters, order_by)
        ret = []
        for a in qs:
            acc = (
                    a.at,
                    a.horse.name,
                    unicode(a.rider.user),
                    unicode(a.type),
                )
            ret.append(acc)
        return (ret, ("count", qs.count()))

reportengine.register(AccidentReport)
