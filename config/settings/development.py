from .base import *

# ======================================================
# DEBUG & SECURITY
# ======================================================
DEBUG = True

SECRET_KEY = env.secrets.SECRET_KEY

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

INTERNAL_IPS = ["127.0.0.1"]


# Add debug context processor
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "django.template.context_processors.debug",
]


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
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


# ======================================================
# CSRF
# ======================================================
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


# ======================================================
# E-MAIL
# ======================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
