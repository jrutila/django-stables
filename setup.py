#!/usr/bin/env python

from setuptools import setup, find_packages
import os

setup(
    name = "django-stables",
    version = "2.0",
    #packages=find_packages(),
    #package_data={ 'stables': data_files},
    author = "Juho Rutila",
    author_email = "juho.rutila@iki.fi",
    description = "Horse stable management package",
    url = "http://rutila.fi",
    install_requires=[
          #"Babel",
          "isoweek>=1.2.0",
          'django-scheduler==0.7.5',
          #'django-reversion==1.7.1',
          'django-sekizai',
          'django-bower',
          'django-crispy-forms',
          'django-reportengine',
          'django-tastypie',
          'django-contrib-comments',
          #'backbone-tastypie',
          #'mimeparse',
          #'djangorestframework',
          'django-phonenumber-field==0.7.2',
          #'django-twilio==0.7',
          #'South==1.0',
          'django-settings',

          # For production
          'django-tenant-schemas'
    ],
    zip_safe=False,
    dependency_links = [
      #'http://github.com/jrutila/django-schedule/tarball/master#egg=django-scheduler-0.7.1-3',
      'http://github.com/jrutila/django-reportengine/tarball/master#egg=django-reportengine-0.3.1.1',
      'http://github.com/jrutila/django-settings/tarball/master#egg=django-settings-1.3.12.999',
      #'http://github.com/jrutila/backbone-tastypie/tarball/master#egg=backbone-tastypie-dev',
    ]
)
