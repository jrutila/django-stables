from django.contrib import admin
from stables_shop.models import TicketProduct, EnrollProduct, EnrollProductActivator, PartShortUrl, \
    ProductAbsoluteDiscount, ProductPercentDiscount
from stables_shop.models import TicketProductActivator


class PartShortUrlAdmin(admin.ModelAdmin):
    raw_id_fields = ('participation',)

#if tenant_schemas.utils.connection.get_tenant().schema_name == 'public':
admin.site.register(TicketProduct)
admin.site.register(TicketProductActivator)
admin.site.register(EnrollProduct)
admin.site.register(EnrollProductActivator)
admin.site.register(PartShortUrl, PartShortUrlAdmin)
admin.site.register(ProductAbsoluteDiscount)
admin.site.register(ProductPercentDiscount)
