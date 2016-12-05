from django.conf.urls import patterns, url, include
from shop import urls

urlpatterns = patterns('',
    include(urls)
)
