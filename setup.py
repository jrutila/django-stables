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
          #"isoweek>=1.2.0",
          #'django-scheduler==0.7.5',
          #'django-sekizai',
          #'django-bower',
          #'django-crispy-forms',
          #'django-reportengine',
          #'django-tastypie',
          #'django-contrib-comments',
          #'django-phonenumber-field==0.7.2',
          #'django-settings',

          # For production
          #'django-tenant-schemas'
    ],
    zip_safe=False,
    dependency_links = [
      #'http://github.com/jrutila/django-reportengine/tarball/master#egg=django-reportengine-0.3.1.1',
      #'http://github.com/jrutila/django-settings/tarball/master#egg=django-settings-1.3.12.999',
    ]
)
