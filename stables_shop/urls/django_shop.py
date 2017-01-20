from django.conf.urls import patterns, url, include
from shop import urls
from stables_shop.serializers import ProductSummarySerializer
from stables_shop.views import ProductListView

urlpatterns = patterns('',
    url('',include(urls)),
    url('products', ProductListView.as_view())
)
