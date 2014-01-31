#!/usr/bin/env python

from setuptools import setup, find_packages
import os

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
myapp_dir = 'stables'

for dirpath, dirnames, filenames in os.walk(myapp_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        for f in filenames:
            data_files.append(os.path.join(dirpath.split('/', 1)[1], f))

setup(
    name = "django-stables",
    version = "dev",
    packages=find_packages(),
    package_data={ 'stables': data_files},
    author = "Juho Rutila",
    author_email = "juho.rutila@iki.fi",
    description = "Horse stable management package",
    url = "http://rutila.fi",
    install_requires=[
      "Babel",
      "isoweek>=1.2.0",
      'django-schedule',
      'django-reversion==1.7.1',
      'django-sekizai',
      'django-crispy-forms',
      'django-reportengine',
      'django-tastypie',
      'backbone-tastypie',
      'mimeparse',
      'djangorestframework',
    ],
    zip_safe=False,
    dependency_links = [
      'http://github.com/jrutila/django-schedule/tarball/master#egg=django-schedule',
      'http://github.com/jrutila/backbone-tastypie/tarball/master#egg=backbone-tastypie-dev',
    ]
)
