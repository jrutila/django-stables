from django.core.management.base import BaseCommand
from customers.models import Client
from django.db import connection
from stables.management.commands.run_activators import Command as ActivatorCommand

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        connection.set_schema('public')
        clients = Client.objects.exclude(schema_name='public')
        for c in clients:
            comm = ActivatorCommand()
            comm.handle(schema=c.schema_name)
