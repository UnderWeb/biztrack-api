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
# LOGGING (more verbose than production)
# ======================================================
LOGGING['root']['level'] = 'DEBUG'
