from .base import *

# ======================================================
# SECURITY
# ======================================================
SECRET_KEY = env.secrets.SECRET_KEY

DEBUG = False

ALLOWED_HOSTS = env.django_conf.ALLOWED_HOSTS


# ======================================================
# DATABASE
# ======================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.database.NAME,
        "USER": env.database.USER,
        "PASSWORD": env.database.PASSWORD,
        "HOST": env.database.HOST,
        "PORT": env.database.PORT,
    }
}


# ======================================================
# CORS
# ======================================================
CORS_ALLOWED_ORIGINS = [
    "https://app-staging.biztrack.cl",
]


# ======================================================
# CSRF
# ======================================================
CSRF_TRUSTED_ORIGINS = [
    "https://app-staging.biztrack.cl",
]


# ======================================================
# LOGGING (more verbose than production)
# ======================================================
LOGGING["root"]["level"] = "DEBUG"
