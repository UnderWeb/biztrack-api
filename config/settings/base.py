"""
Django settings for biztrack API project.
Base settings shared across all environments.

This file:
- Imports all configuration from config.env
- Contains environment-agnostic defaults only
- Does not read os.getenv directly (single source of truth = env.py)
"""

from pathlib import Path
from .. import env


# ======================================================
# PATHS
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ======================================================
# DJANGO CORE APPS
# ======================================================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'django_celery_beat',
]

LOCAL_APPS = []

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ======================================================
# MIDDLEWARE
# ======================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ======================================================
# URLS / WSGI / ASGI CONFIGURATION
# ======================================================
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# ======================================================
# TEMPLATES
# ======================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ======================================================
# PASSWORD VALIDATION
# ======================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ======================================================
# INTERNATIONALIZATION
# ======================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# ======================================================
# DEFAULT PRIMARY KEY
# ======================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ======================================================
# SECURITY
# ======================================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ======================================================
# LOGGING (base minimal configuration; environment can override)
# ======================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# ======================================================
# CACHES (Redis, fails loudly if not configured)
# ======================================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"{env.redis.URL_BASE}/{env.redis.DEFAULT_DB}",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}


# ======================================================
# CELERY
# ======================================================
CELERY_BROKER_URL = env.celery.BROKER_URL
CELERY_RESULT_BACKEND = env.celery.RESULT_BACKEND
CELERY_ACCEPT_CONTENT = env.celery.ACCEPT_CONTENT
CELERY_TASK_SERIALIZER = env.celery.TASK_SERIALIZER
CELERY_RESULT_SERIALIZER = env.celery.RESULT_SERIALIZER
CELERY_TIMEZONE = env.celery.TIMEZONE
CELERY_ENABLE_UTC = env.celery.ENABLE_UTC
CELERY_TASK_TRACK_STARTED = env.celery.TASK_TRACK_STARTED
CELERY_TASK_TIME_LIMIT = env.celery.TASK_TIME_LIMIT
CELERY_BEAT_SCHEDULER = env.celery.BEAT_SCHEDULER

# Django Celery Beat
DJANGO_CELERY_BEAT_TZ_AWARE = env.celery.BEAT_TZ_AWARE
