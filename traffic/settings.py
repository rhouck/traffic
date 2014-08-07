"""
Django settings for traffic project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Use site-specific settings
from socket import gethostname
host = gethostname()
from re import search

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ouytirw%o-&fbs-hdf7db=m$hvd%w*_l9krmk^ic@i5j4js*ms'


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'widget_tweaks',

)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',


)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'django.core.context_processors.request',
    # custom processors
    'traffic.context_processors.google_analytics',)

ROOT_URLCONF = 'traffic.urls'

WSGI_APPLICATION = 'traffic.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)


# register parse
from parse_rest.connection import register
register("DORr1RM1Gyv4UcoT9FRvMniO9A1CnTqxYJ1ty1m0", "QUs3gOoqhPvHUQpjeLYS3V1rW4N3YAtPMaW0vTKx")

if search('heroku', host):
    from settings_live import *
    LIVE = True
    BASE = "http:www.cabtools.com"
else:
    from settings_local import *
    LIVE = False
    BASE = "http://127.0.0.1:8000"

# eventbrite api credentials
EVENTBRITEKEYS = {'app_key':  'EI4VUH4QE3OIQVG27O', 'access_code': 'FSYRI7NFSSVWUV3MTVU5'}

#highrise cms API
HIGHRISE_CONFIG = {'server': 'levelskies', 'auth': 'e8ad8213477f275724c8a90a38bc1f28', 'email': 'dropbox@85120397.levelskies.highrisehq.com'}

# email setup
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'cabtools@gmail.com'
EMAIL_HOST_PASSWORD = '_second&mission_'
DEFAULT_FROM_EMAIL = 'cabtools@gmail.com'

# google analytics
GOOGLE_ANALYTICS_PROPERTY_ID = 'UA-41287666-5'
GOOGLE_ANALYTICS_DOMAIN = 'cabtools.com'
