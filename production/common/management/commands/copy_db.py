from django.core.management import BaseCommand
from django.db import connections
from customers.models import Client

__author__ = 'jorutila'

from collections import namedtuple, OrderedDict


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def insert(data, name, opts):
    colnames = [x for x in data.keys() if "missing" not in opts or x not in opts["missing"]]
    cols = ['"%s"' % x for x in colnames]
    vals = [data[x] for x in colnames]
    vals_str_list = ["%s"] * len(vals)
    vals_str = ", ".join(vals_str_list)

    return ("INSERT INTO {name} ({cols}) VALUES ({vals_str})".format(
                   cols = ", ".join(cols), vals_str = vals_str, name = name), vals)

class Command(BaseCommand):
    help = 'Copy old stables database to the new one'

    def add_arguments(self, parser):
         # Named (optional) arguments
        parser.add_argument('--skip',
            dest='skip',
            default=False,
            help='Skip tenant creation (They should exists already)')
        #parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        c = connections['old'].cursor()
        w = connections['default'].cursor()
        c.execute("SELECT * FROM tenant_client WHERE schema_name != 'public'")
        result = dictfetchall(c)

        if not options["skip"]:
            for tenant in result:
                if (tenant["schema_name"] != "demo"): break
                del tenant["id"]
                t = Client(**tenant)
                t.save()
                self.stdout.write("Created client "+tenant['domain_url'])

        tables = OrderedDict()
        tables['stables_accidenttype'] = {}
        tables['stables_tickettype'] = {}
        tables['auth_user'] = {}
        tables['schedule_calendar'] = {}
        tables['schedule_rule'] = {}
        tables['schedule_event'] = { "missing": ["priority"]}
        tables['schedule_occurrence'] = {}
        tables['shop_cart'] = {}
        tables['shop_cartitem'] = {}
        tables['shop_order'] = {}
        tables['shop_product'] = {}
        tables['shop_orderitem'] = {}
        tables['shop_extraorderpricefield'] = {}
        tables['shop_orderextrainfo'] = {}
        tables['shop_orderpayment'] = {}
        tables['stables_course'] = {}

        for tenant in result:
            skipping = False
            if isinstance(options["skip"], str):
                skipping = options["skip"]
            for (name, t) in tables.items():
                tname = "%s.%s" % (tenant['schema_name'], name)
                if skipping:
                    if skipping == name: skipping = False
                    self.stdout.write("Skipped "+tname)
                    continue
                self.stdout.write("Writing "+tname)
                c.execute("SELECT * FROM %s" % tname)
                data = dictfetchall(c)
                for d in data:
                    (sql, vals) = insert(d, tname, t)
                    w.execute(sql, vals)
