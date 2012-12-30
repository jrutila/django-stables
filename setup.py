#!/usr/bin/env python

from distutils.core import setup
setup(
    name = "django-stables",
    version = "0.0",
    packages = [],
    author = "Juho Rutila",
    author_email = "juho.rutila@iki.fi",
    description = "Horse stable management package",
    url = "http://rutila.fi",
    include_package_data = True,
    install_requires=[
      "isoweek >= 1.2.0"
    ]
)
