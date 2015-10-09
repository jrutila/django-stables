from io import StringIO
from django.contrib.contenttypes.models import ContentType
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




class Command(BaseCommand):
    help = 'Copy old stables database to the new one'

    def add_arguments(self, parser):
         # Named (optional) arguments
        parser.add_argument('--skip',
            dest='skip',
            default=False,
            help='Skip the db tables till')
        parser.add_argument('--tenant',
            dest='tenant',
            default=False,
            help='Run only this tenant')
        #parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        c = connections['old'].cursor()
        w = connections['default'].cursor()
        c.execute("SELECT * FROM tenant_client WHERE schema_name != 'public'")
        result = dictfetchall(c)

        tables = OrderedDict()
        tables['stables_accidenttype'] = {}
        tables['stables_tickettype'] = {}
        tables['auth_user'] = {}
        tables['schedule_calendar'] = {}
        tables['schedule_rule'] = {}
        tables['schedule_event'] = { "missing": ["priority"]}
        tables['schedule_occurrence'] = {}
        tables['stables_shop_product'] = { "convert": { "polymorphic_ctype_id": "content_type" }}
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
        tables['stables_riderlevel'] = {}
        tables['stables_course_allowed_levels'] = {}
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
        tables['stables_shop_ticketproduct'] = { "convert": { "duration": lambda x: "%s second" % int(x/1000000) if x else "\\N" }}
        tables['stables_shop_ticketproductactivator'] = { "convert": { "duration": lambda x: "%s second" % int(x/1000000) if x else "\\N" }}
        tables['stables_transaction'] = {}
        tables['stables_ticket'] = {}
        tables['django_settings_setting'] = { "convert": { "setting_type_id": "content_type" }}
        tables['django_settings_email'] = {}
        tables['django_settings_integer'] = {}
        tables['django_settings_longstring'] = { "table": "stables_shop_longstring" }
        tables['django_settings_positiveinteger'] = {}
        tables['django_settings_string'] = {}

        for tenant in result:

            if "tenant" in options:
                if (options["tenant"] and tenant["schema_name"] != options["tenant"]):
                    continue

            connections["default"].set_schema("public")
            if not options["skip"]:
                #if (tenant["schema_name"] != "demo"): break
                del tenant["id"]
                t = Client(**tenant)
                t.save()
                self.stdout.write("Created client "+tenant['domain_url'])

            connections["old"].set_schema(tenant["schema_name"])
            connections["default"].set_schema(tenant["schema_name"])

            skipping = False
            if isinstance(options["skip"], str):
                skipping = options["skip"]
            for (name, t) in tables.items():
                tname = "%s.%s" % (tenant['schema_name'], name)
                if skipping and skipping != "True":
                    if skipping == name: skipping = False
                    self.stdout.write("Skipped "+tname)
                    continue
                toname = tenant["schema_name"]+"."+t["table"] if "table" in t else tname
                c.execute("SELECT * FROM %s" % tname)
                data = dictfetchall(c)
                opts = t
                fd = ""
                conv = opts["convert"] if "convert" in opts else None
                counter = 0
                if (len(data)):
                    self.stdout.write("Writing %s to %s" % (tname, toname))
                    colnames = [x for x in data[0].keys() if "missing" not in opts or x not in opts["missing"]]
                    for d in data:
                        counter = counter + 1
                        vals = []
                        for x in colnames:
                            dd = d[x]
                            if conv and x in conv:
                                if (conv[x] == "content_type"):
                                    oldct = ContentType.objects.using("old").get(id=dd)
                                    newct = ContentType.objects.using("default").get(model=oldct.model)
                                    vals.append(newct.id)
                                else:
                                    vals.append(conv[x](dd))
                            else:
                                vals.append(default_conv(dd))
                        #vals = [conv[x](d[x]) if conv and x in conv else default_conv(d[x]) for x in colnames]
                        fd = str(fd) + "\t".join([str(x) for x in vals]) + "\n"
                        #(sql, vals) = insert(d, toname, t)
                        #w.execute(sql, vals)
                    self.stdout.write(",".join(colnames) + " -> "+toname)
                    self.stdout.write(fd)
                    w.copy_from(StringIO(fd), toname, columns=['"'+x+'"' for x in colnames])
                else:
                    self.stdout.write("No data for %s" % toname)

def default_conv(value):
    if str(value) == "True":
        return "t"
    if str(value) == "False":
        return "f"
    if value == None:
        return "\\N"
    return str(value).strip().replace("\r", "").replace("\n", "\\n")
