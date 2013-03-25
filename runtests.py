'''
DATABASES = {
    'default': {
      'ENGINE': 'sqlite3',
    }
}
from django_runtests import RunTests

def runtests():
    return RunTests.runtests()

if __name__ == "__main__":
  RunTests.main()
'''
import os, sys
from django.conf import settings

DIRNAME = os.path.dirname(__file__)
settings.configure(DEBUG=True,
               DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                    }
                },
               ROOT_URLCONF='stables.urls',
               AUTH_PROFILE_MODULE='stables.UserProfile',
               INSTALLED_APPS=('django.contrib.auth',
                              'django.contrib.contenttypes',
                              'django.contrib.sessions',
                              'django.contrib.admin',
                              'schedule',
                              'stables',
                              'filer',
                              'taggit',
                              'reversion',
                              'django_nose',
                              ))

from django.test.simple import DjangoTestSuiteRunner
test_runner = DjangoTestSuiteRunner(verbosity=1, failfast=False)
#import django_nose
#test_runner = django_nose.NoseTestSuiteRunner(verbosity=1)
failures = test_runner.run_tests(['stables', ])
if failures:
    sys.exit(failures)
