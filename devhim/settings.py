"""
Django settings for devhim_dev project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+5f+e2!cqar%$u$#&(r_^1dv40_p-d_qsr#=&xmw2!wmp_0)u7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'activeBPM'
]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'devhim.urls'

WSGI_APPLICATION = 'devhim.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/
TIME_ZONE = 'Europe/Kiev'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru'

USE_I18N = False

USE_L10N = False

USE_TZ = False

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request"

)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR + '/devhim/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR + '/devhim/media/'

TEMPLATE_DIRS = (
)

from django.core.urlresolvers import reverse_lazy

LOGIN_URL = reverse_lazy('admin:login')
LOGIN_REDIRECT_URL = '/'


#---profiler SILK
#ENABLE_SILK = True
#SILKY_META = True
#SILKY_PYTHON_PROFILER = True
#MIDDLEWARE_CLASSES = ['silk.middleware.SilkyMiddleware'] + MIDDLEWARE_CLASSES
#INSTALLED_APPS += ['silk']

#---email
EMAIL_HOST_USER = 'ukrhimplast_notifier@ukrhimplast.com'
EMAIL_HOST_PASSWORD = '777777'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 587
EMAIL_USE_TLS = True


#---celery (need to be included in wsgi too)
import djcelery
djcelery.setup_loader()
INSTALLED_APPS += ['djcelery']
BROKER_URL = 'django://'
INSTALLED_APPS += ['kombu.transport.django']
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"