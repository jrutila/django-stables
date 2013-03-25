#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name = "django-stables",
    version = "0.0.1",
    packages=find_packages(),
    include_package_data=True,
    author = "Juho Rutila",
    author_email = "juho.rutila@iki.fi",
    description = "Horse stable management package",
    url = "http://rutila.fi",
    install_requires=[
      "Babel",
      "isoweek>=1.2.0",
      'django-schedule',
      'django-reversion',
      'easy-thumbnails',
      'django-filer',
      'django-taggit',
      'simple_translation',
      'south',
      'PIL',
      'django-reversion',
    ],
    dependency_links = [
      'http://github.com/jrutila/django-schedule/tarball/master#egg=django-schedule',
      'http://github.com/jrutila/django-filer/tarball/master#egg=django-filer',
    ]

)
