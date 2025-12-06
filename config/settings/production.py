from .base import *


# ======================================================
# SECURITY
# ======================================================
DEBUG = False
SECRET_KEY = env.secrets.SECRET_KEY

# Allowed hosts must be explicitly defined in production
ALLOWED_HOSTS = env.django_conf.ALLOWED_HOSTS

# Enforce HTTPS (recommended for AWS, GCP, etc.)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000 # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ======================================================
# DATABASE
# ======================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.database.NAME,
        'USER': env.database.USER,
        'PASSWORD': env.database.PASSWORD,
        'HOST': env.database.HOST,
        'PORT': env.database.PORT,
    }
}


# ======================================================
# CORS
# ======================================================
CORS_ALLOWED_ORIGINS = [
    "https://app.biztrack.cl",
]


# ======================================================
# CSRF
# ======================================================
CSRF_TRUSTED_ORIGINS = [
    "https://app.biztrack.cl",
    "https://*.biztrack.cl",  # optional wildcard if subdomains exist
]
