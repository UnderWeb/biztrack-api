"""
Django settings for biztrack API project.
Base settings shared across all environments.

This file:
- Imports all configuration from config.env
- Contains environment-agnostic defaults only
- Does not read os.getenv directly (single source of truth = env.py)
"""

from datetime import timedelta
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
    'drf_spectacular',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
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
USE_THOUSAND_SEPARATOR = True
USE_TZ = False


# ======================================================
# DEFAULT PRIMARY KEY
# ======================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ======================================================
# DJANGO REST FRAMEWORK
# ======================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'config.pagination.StandardResultsPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# ================================================
# DRF Spectacular (OpenAPI Schema)
# ================================================
SPECTACULAR_SETTINGS = {
    # ---- BASIC METADATA ----
    "TITLE": "BizTrack API",
    "DESCRIPTION": (
        "BizTrack — Business management platform.\n\n"
        "Documentation automatically generated with OpenAPI 3."
    ),
    "VERSION": "1.0.0",
    "CONTACT": {
        "name": env.project.NAME,
        "url": env.project.URL,
        "email": env.project.EMAIL,
    },

    # ---- SCHEMA ----
    "SERVE_INCLUDE_SCHEMA": False,  # /schema/ solo sirve el esquema, no la UI
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    "CAMELIZE_NAMES": False,  # True si quieres camelCase en los docs

    # ---- COMPONENTES & AUTH ----
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,

    "SECURITY": [
        {"BearerAuth": []},  # Para JWT
    ],
    "SECURITY_SCHEMES": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    },

    # ---- SWAGGER UI ----
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,  # barra de búsqueda
        "tryItOutEnabled": True,
    },

    # Puedes cambiar la versión del CDN si quieres
    "SWAGGER_UI_DIST": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest",

    # favicon propio opcional
    # "SWAGGER_UI_FAVICON_HREF": settings.STATIC_URL + "biztrack_favicon.png",

    # ---- REDOC ----
    "REDOC_DIST": "https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js",

    # ---- GENERACIÓN DEL ESQUEMA ----
    "PREPROCESSING_HOOKS": [],
    "POSTPROCESSING_HOOKS": [],
    "SERVE_PERMISSIONS": [],  # por defecto sin auth para docs
}


# ======================================================
# JWT
# ======================================================
SIMPLE_JWT = {
    # lifetimes
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.jwt.ACCESS_TOKEN_LIFETIME_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.jwt.REFRESH_TOKEN_LIFETIME_DAYS),

    # rotation & blacklist (recommended for BizTrack)
    "ROTATE_REFRESH_TOKENS": env.jwt.ROTATE_REFRESH_TOKENS,
    "BLACKLIST_AFTER_ROTATION": env.jwt.BLACKLIST_AFTER_ROTATION,
    "UPDATE_LAST_LOGIN": False,

    # crypto
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env.secrets.SECRET_KEY,  # or use an env-only JWT_SIGNING_KEY if preferred
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "LEEWAY": 0,

    # auth header
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",

    # user lookup
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    # optional sliding tokens (not used by default)
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    # serializers (defaults ok)
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
}


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
