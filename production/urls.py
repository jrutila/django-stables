"""example URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from production.common.forms import EmailAuthenticationForm

urlpatterns = [
    url('^admin/', include(admin.site.urls)),
    url('^', include("stables.urls")),
    url('^s/', include("stables_shop.urls")),
    url('^shop/', include("stables_shop.shop_urls")),
    url('^api/', include('stables.urls.api')),
    url('^api-help/', 'production.common.views.api', name='api-help'),
    url('^', include('django.contrib.auth.urls')),
    url('^accounts/login/$', 'django.contrib.auth.views.login', { 'authentication_form': EmailAuthenticationForm }, name='login'),
]
