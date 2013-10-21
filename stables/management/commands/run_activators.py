from django.core.management.base import BaseCommand
from stables.models import ParticipationTransactionActivator, CourseTransactionActivator, CourseParticipationActivator
from stables.models import Participation
import reversion
from django.db import connection
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--schema', dest='schema'),
            )
    def handle(self, *args, **options):
        schema = options['schema']
        connection.set_schema(schema)
        reversion.register(Participation)
        self.activate_transactions()

    @reversion.create_revision()
    def activate_transactions(self):
        for e in CourseParticipationActivator.objects.all():
            e.try_activate()
        for p in ParticipationTransactionActivator.objects.all():
            p.try_activate()
        for c in CourseTransactionActivator.objects.all():
            c.try_activate()

