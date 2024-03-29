from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection
from optparse import make_option
from stables.models.financial import ParticipationTransactionActivator
from stables.models.participations import CourseParticipationActivator, ParticipationError


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--schema', dest='schema'),
            )
    def handle(self, *args, **options):
        schema = options['schema']
        connection.set_schema(schema)
        #reversion.register(Participation)
        ContentType.objects.clear_cache()
        self.activate_transactions()

    def activate_transactions(self):
        for e in CourseParticipationActivator.objects.all():
            try:
                e.try_activate()
            except ParticipationError:
                pass
        for p in ParticipationTransactionActivator.objects.all():
            p.try_activate()
        #for c in CourseTransactionActivator.objects.all():
            #c.try_activate()

