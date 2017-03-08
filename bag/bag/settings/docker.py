import os
import re

from .settings import *

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

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
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },

    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },

    'loggers': {
        # Debug all batch jobs
        'batch': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },

        'search': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        'elasticsearch': {
            'handlers': ['console'],
            'level': 'ERROR',
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

STATIC_ROOT = '/static/'

DIVA_DIR = '/app/data/'

# Generate https links
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
