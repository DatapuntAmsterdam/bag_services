import os
import sys
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from bag.settings.settings_common import *  # noqa F403
from bag.authorization_levels import all_options


from bag.settings.settings_databases import LocationKey,\
    get_docker_host,\
    get_database_key,\
    OVERRIDE_HOST_ENV_VAR,\
    OVERRIDE_PORT_ENV_VAR

from .checks import check_elasticsearch  # noqa
from .checks import check_database  # noqa


NO_INTEGRATION_TEST = os.getenv('NO_INTEGRATION_TEST', True)
NO_INTEGATION_TEST = True

# Application definition
PARTIAL_IMPORT = dict(
    numerator=0,
    denominator=1
)

STATIC_ROOT = 'static/'
STATIC_URL = '/static/'

ROOT_URLCONF = 'bag.urls'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASE_OPTIONS = {
    LocationKey.docker: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'bag_v11'),
        'USER': os.getenv('DATABASE_USER', 'bag_v11'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': 'database',
        'PORT': '5432',
        'CONN_MAX_AGE': 30,
    },
    LocationKey.local: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'bag_v11'),
        'USER': os.getenv('DATABASE_USER', 'bag_v11'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': get_docker_host(),
        'PORT': '5434',
        'CONN_MAX_AGE': 30,
    },
    LocationKey.override: {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'bag_v11'),
        'USER': os.getenv('DATABASE_USER', 'bag_v11'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'insecure'),
        'HOST': os.getenv(OVERRIDE_HOST_ENV_VAR),
        'PORT': os.getenv(OVERRIDE_PORT_ENV_VAR, '5432'),
        'CONN_MAX_AGE': 30,
    },
}

DATABASES = {
    'default': DATABASE_OPTIONS[get_database_key()]
}

EL_HOST_VAR = os.getenv('ELASTIC_HOST_OVERRIDE')

EL_PORT_VAR = os.getenv('ELASTIC_PORT_OVERRIDE', '9200')

ELASTIC_OPTIONS = {
    LocationKey.docker: ["http://elasticsearch:9200"],
    LocationKey.local: [f"http://{get_docker_host()}:9200"],
    LocationKey.override: [f"http://{EL_HOST_VAR}:{EL_PORT_VAR}"],
}

ELASTIC_SEARCH_HOSTS = ELASTIC_OPTIONS[get_database_key()]

ELASTIC_INDICES = {
    'BAG_GEBIED': 'bag_v11_gebied',
    'BAG_BOUWBLOK': 'bag_v11_bouwblok',
    'BRK_OBJECT': 'brk_v11_object',
    'BRK_SUBJECT': 'brk_v11_subject',
    'NUMMERAANDUIDING': 'v11_nummeraanduiding',
    'BAG_PAND': 'bag_v11_pand',
}

TESTING = 'pytest' in sys.modules or (len(sys.argv) > 1 and sys.argv[1] == 'test')
if TESTING:
    for k, v in ELASTIC_INDICES.items():
        ELASTIC_INDICES[k] = f'test_{v}'

BATCH_SETTINGS = dict(
    batch_size=5000
)


ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.localdomain',
    '.data.amsterdam.nl',
    'bag-api.service.consul',
    'bag_v11-api.service.consul',
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


SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'


swag_path = 'https://acc.api.data.amsterdam.nl/bag/docs'

if DEBUG:
    swag_path = '127.0.0.1:8000/bag/docs'


SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': '0.1',
    'api_path': '/',

    'enabled_methods': [
        'get',
    ],

    'api_key': '',
    'USE_SESSION_AUTH': False,
    'VALIDATOR_URL': None,

    'is_authenticated': False,
    'is_superuser': False,

    'unauthenticated_user': 'django.contrib.auth.models.AnonymousUser',
    'permission_denied_handler': None,
    'resource_access_handler': None,

    'protocol': 'https' if not DEBUG else '',
    'base_path': swag_path,

    'info': {
        'contact': 'atlas.basisinformatie@amsterdam.nl',
        'description': 'This is the BAG API server.',
        'license': 'Mozilla Public License Version 2.0',
        'licenseUrl': 'https://www.mozilla.org/en-US/MPL/2.0/',
        'termsOfServiceUrl': 'https://data.amsterdam.nl/terms/',
        'title': 'BAG, BRK en WKPB API',
    },

    'doc_expansion': 'list',

    'SECURITY_DEFINITIONS': {
        'oauth2': {
            'type': 'oauth2',
            'authorizationUrl':
                DATAPUNT_API_URL + "oauth2/authorize",
            'flow': 'implicit',
            'scopes': all_options
        }
    }
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

PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))

DIVA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'data'))
GOB_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'data/gob'))
# DIVA_DIR = '/app/data'

if not os.path.exists(DIVA_DIR):
    DIVA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'bag', 'diva'))
    print("Geen lokale DIVA bestanden gevonden, maak gebruik van testset",
          DIVA_DIR, "\n")


# The following JWKS data was obtained in the authz project :
# jwkgen -create -alg ES256
# This is a test public/private key def and added for testing .
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
    # 'ALWAYS_OK': True,  # disable authz. tests will fail...
    'JWKS': os.getenv('PUB_JWKS', JWKS_TEST_KEY),
    'JWKS_URL': os.getenv('KEYCLOAK_JWKS_URL')
}

SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment='bag_services',
        ignore_errors=['ExpiredSignatureError']
    )

FEATURE_2 = 2
