from django.contrib import admin
from models import TicketProduct, PartShortUrl
from models import TicketProductActivator
from models import EnrollProduct
from models import EnrollProductActivator
from django.db import models
from django.forms import forms

class PartShortUrlAdmin(admin.ModelAdmin):
    raw_id_fields = ('participation',)

#if tenant_schemas.utils.connection.get_tenant().schema_name == 'public':
admin.site.register(TicketProduct)
admin.site.register(TicketProductActivator)
admin.site.register(EnrollProduct)
admin.site.register(EnrollProductActivator)
admin.site.register(PartShortUrl, PartShortUrlAdmin)
