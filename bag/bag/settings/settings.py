"""
Django settings for BAG project.

Basis Administratie Gebouwen

Generated by 'django-admin startproject' using Django 1.8.3.

more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

from bag.settings.settings_databases import LocationKey, \
    get_docker_host, \
    get_database_key, \
    OVERRIDE_HOST_ENV_VAR, \
    OVERRIDE_PORT_ENV_VAR

NO_INTEGRATION_TEST = os.getenv('NO_INTEGRATION_TEST', True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
insecure_key = 'insecure'

SECRET_KEY = os.getenv('BAG_SECRET_KEY', insecure_key)

DEBUG = SECRET_KEY == insecure_key

# Application definition
PARTIAL_IMPORT = dict(
    numerator=0,
    denominator=1
)
STATIC_ROOT = 'static/'


NO_INTEGATION_TEST = True

DATAPUNT_API_URL = os.getenv(
    # note the ending /
    'DATAPUNT_API_URL', 'https://api.data.amsterdam.nl/')

INSTALLED_APPS = (
    'django.contrib.contenttypes',

    'django.contrib.staticfiles',
    'django_extensions',
    'django_filters',

    'batch',
    'bag_commands',

    'datasets.bag',
    'datasets.brk',
    'datasets.wkpb',

    'geo_views',
    'datapunt_api',      # main entry, search urls
    'health',

    'django.contrib.gis',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework_swagger',
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'authorization_django.authorization_middleware',
)

if DEBUG:
    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

ROOT_URLCONF = 'bag.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bag.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASE_OPTIONS = {
    LocationKey.docker: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'atlas'),
        'USER': os.getenv('DATABASE_USER', 'atlas'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': 'database',
        'PORT': '5432'
    },
    LocationKey.local: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'atlas'),
        'USER': os.getenv('DATABASE_USER', 'atlas'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': get_docker_host(),
        'PORT': '5434'
    },
    LocationKey.override: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'atlas'),
        'USER': os.getenv('DATABASE_USER', 'atlas'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv(OVERRIDE_HOST_ENV_VAR, get_docker_host()),
        'PORT': os.getenv(OVERRIDE_PORT_ENV_VAR, 5434),
        'CONN_MAX_AGE': 30,
    }
}

DATABASES = {
    'default': DATABASE_OPTIONS[get_database_key()]
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

ELASTIC_INDICES = {
    'BAG': 'bag',
    'BRK': 'brk',
    'NUMMERAANDUIDING': 'nummeraanduiding',
}

if TESTING:
    for k, v in ELASTIC_INDICES.items():
        ELASTIC_INDICES[k] += 'test'

ELASTIC_SEARCH_HOSTS = ["{}:{}".format(
    os.getenv('ELASTICSEARCH_PORT_9200_TCP_ADDR', get_docker_host()),
    os.getenv('ELASTICSEARCH_PORT_9200_TCP_PORT', 9200))]

BATCH_SETTINGS = dict(
    batch_size=4000
)

STATIC_URL = '/static/'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.localdomain',
    '.data.amsterdam.nl',
    'bag-api.service.consul',
    '.amsterdam.nl',
    '.service.consul',
]

REST_FRAMEWORK = dict(
    PAGE_SIZE=25,
    MAX_PAGINATE_BY=100,

    UNAUTHENTICATED_USER={},
    UNAUTHENTICATED_TOKEN={},

    DEFAULT_PAGINATION_CLASS='drf_hal_json.pagination.HalPageNumberPagination',
    DEFAULT_PARSER_CLASSES=(
        'drf_hal_json.parsers.JsonHalParser',
    ),
    DEFAULT_RENDERER_CLASSES=(
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ),
    DEFAULT_FILTER_BACKENDS=(
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
)

# The following JWKS data was obtained in the authz project :  jwkgen -create -alg ES256
# This is a test public key def. The private key is add for testing.
JWKS_TEST_KEY = """
{
    "keys": [
        {
            "kty": "EC",
            "key_ops": [
                "verify",
                "sign"
            ],
            "kid": "2aedafba-8170-4064-b704-ce92b7c89cc6",
            "crv": "P-256",
            "x": "6r8PYwqfZbq_QzoMA4tzJJsYUIIXdeyPA27qTgEJCDw=",
            "y": "Cf2clfAfFuuCB06NMfIat9ultkMyrMQO9Hd2H7O9ZVE=",
            "d": "N1vu0UQUp0vLfaNeM0EDbl4quvvL6m_ltjoAXXzkI3U="
        }
    ]
}
"""

DATAPUNT_AUTHZ = {
    'JWKS': os.getenv('PUB_JWKS', JWKS_TEST_KEY)
}

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': '0.1',
    'api_path': '/',

    'enabled_methods': [
        'get',
    ],

    'USE_SESSION_AUTH': False,
    'VALIDATOR_URL': None,

    'api_key': '',

    'is_authenticated': False,
    'is_superuser': False,

    'permission_denied_handler': None,
    'resource_access_handler': None,

    'protocol': 'https' if not DEBUG else '',
    'base_path': 'acc.api.data.amsterdam.nl/bag/docs' if DEBUG else '127.0.0.1:8000/bag/docs',  # noqa

    'info': {
        'contact': 'atlas.basisinformatie@amsterdam.nl',
        'description': 'This is the BAG API server.',
        'license': 'Mozilla Public License Version 2.0',
        'licenseUrl': 'https://www.mozilla.org/en-US/MPL/2.0/',
        'termsOfServiceUrl': 'https://data.amsterdam.nl/terms/',
        'title': 'BAG, BRK en WKPB API',
    },
    'doc_expansion': 'list',
}

OBJECTSTORE = {
    'auth_version': '2.0',
    'authurl': 'https://identity.stack.cloudvps.com/v2.0',
    'user': os.getenv('OBJECTSTORE_USER', 'bag_brk'),
    'key': os.getenv('BAG_OBJECTSTORE_PASSWORD', 'insecure'),
    'tenant_name': 'BGE000081_BAG',
    'os_options': {
        'tenant_id': '4f2f4b6342444c84b3580584587cfd18',
        'region_name': 'NL',
        'endpoint_type': 'internalURL'
    }
}


LOGSTASH_HOST = os.getenv('LOGSTASH_HOST', '127.0.0.1')
LOGSTASH_PORT = int(os.getenv('LOGSTASH_GELF_UDP_PORT', 12201))


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'formatters': {
        'slack': {
            'format': '%(message)s',
        },
        'console': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },

    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },

        'graypy': {
            'level': 'ERROR',
            'class': 'graypy.GELFHandler',
            'host': LOGSTASH_HOST,
            'port': LOGSTASH_PORT,
        },

    },

    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'graypy'],
    },

    'loggers': {
        # Debug all batch jobs
        'batch': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'search': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'elasticsearch': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'urllib3.connectionpool': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        # Log all unhandled exceptions
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))

DIVA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'data'))

if not os.path.exists(DIVA_DIR):
    DIVA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'bag', 'diva'))
    print("Geen lokale DIVA bestanden gevonden, maak gebruik van testset",
          DIVA_DIR, "\n")

# noinspection PyUnresolvedReferences
from .checks import *  # used for ./manage.py check  # noqa
