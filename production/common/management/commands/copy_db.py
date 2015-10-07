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
    conv = opts["convert"] if "convert" in opts else None
    colnames = [x for x in data.keys() if "missing" not in opts or x not in opts["missing"]]
    cols = ['"%s"' % x for x in colnames]
    vals = [conv[x](data[x]) if conv and x in conv else data[x] for x in colnames]
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
        tables['stables_shop_product'] = { }
        tables['shop_cart'] = {}
        tables['shop_cartitem'] = {}
        tables['shop_order'] = {}
        tables['shop_orderitem'] = {}
        tables['shop_extraorderpricefield'] = {}
        tables['shop_orderextrainfo'] = {}
        tables['shop_orderpayment'] = {}
        tables['stables_course'] = {}
        tables['stables_horse'] = {}
        tables['stables_instructorinfo'] = {}
        tables['stables_customerinfo'] = {}
        tables['stables_riderinfo'] = {}
        tables['stables_accident'] = {}
        tables['stables_course_allowed_levels'] = {}
        tables['stables_riderlevel'] = {}
        tables['stables_course_events'] = {}
        tables['stables_course_ticket_type'] = {}
        tables['stables_userprofile'] = {}
        tables['stables_enroll'] = {}
        tables['stables_courseparticipationactivator'] = {}
        #tables['stables_coursetransactionactivator'] = {}
        tables['stables_eventmetadata'] = {}
        tables['stables_instructorparticipation'] = {}
        tables['stables_participation'] = {}
        tables['stables_participationtransactionactivator'] = {}
        tables['stables_participationtransactionactivator_ticket_type'] = {}
        tables['stables_riderinfo_levels'] = {}
        tables['stables_riderlevel_includes'] = {}
        tables['stables_shop_address'] = {}
        tables['stables_shop_digitalshippingaddressmodel'] = {}
        tables['stables_shop_enrollproduct'] = {}
        tables['stables_shop_enrollproductactivator'] = {}
        tables['stables_shop_partshorturl'] = {}
        tables['stables_shop_productactivator'] = {}
        tables['stables_shop_ticketproduct'] = { "convert": { "duration": lambda x: "%s second" % int(x/1000000) }}
        tables['stables_shop_ticketproductactivator'] = {}
        tables['stables_transaction'] = {}
        tables['stables_ticket'] = {}

        for tenant in result:
            skipping = False
            if isinstance(options["skip"], str):
                skipping = options["skip"]
            for (name, t) in tables.items():
                tname = "%s.%s" % (tenant['schema_name'], name)
                if skipping and skipping != "True":
                    if skipping == name: skipping = False
                    self.stdout.write("Skipped "+tname)
                    continue
                toname = t["table"] if "table" in t else tname
                self.stdout.write("Writing %s to %s" % (tname, toname))
                c.execute("SELECT * FROM %s" % tname)
                data = dictfetchall(c)
                for d in data:
                    (sql, vals) = insert(d, toname, t)
                    w.execute(sql, vals)
