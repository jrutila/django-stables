from django.contrib import admin
from .models.product import TicketProduct, EnrollProduct
from .models.activator import EnrollProductActivator, PartShortUrl, TicketProductActivator
from .models.discount import ProductAbsoluteDiscount, ProductPercentDiscount, WholePercentDiscount

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
admin.site.register(WholePercentDiscount)
