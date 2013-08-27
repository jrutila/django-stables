#!/usr/bin/env python

from setuptools import setup, find_packages
setup(
    name = "django-stables",
    version = "dev",
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
      'django-sekizai',
      'django-crispy-forms',
      'django-reporting',
    ],
    zip_ok=False,
    dependency_links = [
      'http://github.com/jrutila/django-schedule/tarball/master#egg=django-schedule',
      'http://github.com/jrutila/django-filer/tarball/master#egg=django-filer',
      'http://github.com/jrutila/django-reporting/tarball/master#egg=django-reporting',
    ]

)
