from .base import *


# ======================================================
# DEBUG & SECURITY
# ======================================================
DEBUG = True

SECRET_KEY = env.secrets.SECRET_KEY

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

INTERNAL_IPS = ['127.0.0.1']


# Add debug context processor
TEMPLATES[0]['OPTIONS']['context_processors'] += [
'django.template.context_processors.debug',
]


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
# STATIC & MEDIA FILES
# ======================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
