# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import socket

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# openshift is our PAAS for now.
ON_PAAS = 'OPENSHIFT_REPO_DIR' in os.environ

if ON_PAAS:
    SECRET_KEY = os.environ['OPENSHIFT_SECRET_TOKEN']
else:
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = ')_7av^!cy(wfx=666666666666zv+ot^1@sh9s9t=8$bu@r(z$'

# SECURITY WARNING: don't run with debug turned on in production!
# adjust to turn off when on Openshift, but allow an environment variable to override on PAAS
DEBUG = not ON_PAAS
DEBUG = DEBUG or os.getenv("debug","false").lower() == "true"

if ON_PAAS and DEBUG:
    print("*** Warning - Debug mode is on ***")

if ON_PAAS:
    ALLOWED_HOSTS = [os.environ['OPENSHIFT_APP_DNS'], socket.gethostname()]
else:
    ALLOWED_HOSTS = []

if not ON_PAAS:
    MERCHANT_ID="13466"
    MERCHANT_PASS="6pKF4jkv97zmqBJ3ZL8gUw5DfT2NMQ"


# Application definition
SHARED_APPS = (
    'tenant_schemas',  # mandatory
    'customers', # you must list the app where your tenant model resides in

    'production.common',

    'django.contrib.contenttypes',
    'django.contrib.staticfiles',

    'djangobower',
    'crispy_forms',
    'sekizai',
    'rest_framework',

    # everything below here is optional
    #'django.contrib.admin',
    'django.contrib.auth',
)

if DEBUG and not ON_PAAS:
  SHARED_APPS = SHARED_APPS + ('debug_toolbar',)
  

TENANT_APPS = (
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',
    'django.contrib.messages',

    # Optional Django
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',

    # your tenant-specific apps
    'stables',
    'schedule',
    'reportengine',

    'shop',
    'stables_shop',
    'discount',
    'discount.default_discounts',

    'django_settings'
)

INSTALLED_APPS = list(set(TENANT_APPS + SHARED_APPS))

TENANT_MODEL = "customers.Client"

BOWER_INSTALLED_APPS = (
    # Required for functionality
    'jquery#1.11.3',
    'jquery.cookie',
    'jquery-ui',
    'backbone',
    'backbone.do',
    'backbone-tastypie',
    'underscore',
    'moment',
    'font-awesome',
    'bootstrap',
    'jquery-slugify',
    'datatables',

    # Required for base admin
)
if ON_PAAS and 'OPENSHIFT_BOWER_PATH' in os.environ:
    BOWER_PATH = os.environ['OPENSHIFT_BOWER_PATH']
if ON_PAAS:
    BOWER_COMPONENTS_ROOT = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'components')

MIDDLEWARE_CLASSES = (
    'tenant_schemas.middleware.TenantMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', 'customers.auth_backends.MasterUserBackend')

ROOT_URLCONF = 'production.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'production', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.core.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sekizai.context_processors.sekizai',
            ],
            'debug': DEBUG,
        },
    },
]

CRISPY_TEMPLATE_PACK = 'bootstrap3'
# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

if ON_PAAS:
    # determine if we are on MySQL or POSTGRESQL
    if "OPENSHIFT_POSTGRESQL_DB_USERNAME" in os.environ: 
    
        DATABASES = {
            'default': {
                #'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'ENGINE': 'tenant_schemas.postgresql_backend',
                'NAME':     os.environ['OPENSHIFT_APP_NAME'],
                'USER':     os.environ['OPENSHIFT_POSTGRESQL_DB_USERNAME'],
                'PASSWORD': os.environ['OPENSHIFT_POSTGRESQL_DB_PASSWORD'],
                'HOST':     os.environ['OPENSHIFT_POSTGRESQL_DB_HOST'],
                'PORT':     os.environ['OPENSHIFT_POSTGRESQL_DB_PORT'],
            },
            'old': {
                'ENGINE': 'tenant_schemas.postgresql_backend',
                'NAME':     os.environ['OPENSHIFT_OLD_APP_NAME'],
                'USER':     os.environ['OPENSHIFT_OLD_POSTGRESQL_DB_USERNAME'],
                'PASSWORD': os.environ['OPENSHIFT_OLD_POSTGRESQL_DB_PASSWORD'],
                'HOST':     os.environ['OPENSHIFT_OLD_POSTGRESQL_DB_HOST'],
                'PORT':     os.environ['OPENSHIFT_OLD_POSTGRESQL_DB_PORT'],
            }
        }
        
    elif "OPENSHIFT_MYSQL_DB_USERNAME" in os.environ: 
    
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME':     os.environ['OPENSHIFT_APP_NAME'],
                'USER':     os.environ['OPENSHIFT_MYSQL_DB_USERNAME'],
                'PASSWORD': os.environ['OPENSHIFT_MYSQL_DB_PASSWORD'],
                'HOST':     os.environ['OPENSHIFT_MYSQL_DB_HOST'],
                'PORT':     os.environ['OPENSHIFT_MYSQL_DB_PORT'],
            }
        }

        
else:
    # stock django, local development.
    DATABASES = {
        'default': {
            'ENGINE': 'tenant_schemas.postgresql_backend',
            'NAME': 'tenant',
            'USER': 'talli',
            'PASSWORD': '',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        },
        'old': {
            'ENGINE': 'tenant_schemas.postgresql_backend',
            'NAME': 'talli',
            'USER': 'talli',
            'PASSWORD': '',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }

DATABASE_ROUTERS = (
    'tenant_schemas.routers.TenantSyncRouter',
)

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/
LANGUAGE_CODE = 'fi-fi'

TIME_ZONE = 'Europe/Helsinki'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SHOP_APP_LABEL = 'stables_shop'
SHOP_ADDRESS_MODEL = 'stables_shop.addressmodel.Address'
SHOP_SHIPPING_BACKENDS = ['stables_shop.backends.DigitalShipping',]
SHOP_PAYMENT_BACKENDS = ['stables_shop.backends.PayTrailBackend', 'shop.payment.backends.prepayment.ForwardFundBackend']
SHOP_CART_MODIFIERS = ['discount.cart_modifiers.DiscountCartModifier','stables_shop.modifiers.FixedVATRate',]
SHOP_PRODUCT_MODEL = ('stables_shop.product.Product', 'stables_shop')
from decimal import Decimal
SHOP_VAT = Decimal('0.10')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'wsgi','static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR,"static"),
    os.path.join(BASE_DIR,"production","static"),
)

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login'

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    #EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    #EMAIL_FILE_PATH = '/tmp/app-messages'


