"""
Production settings for Render + Neon.tech
"""
from .base import *
import os
import dj_database_url
# SECURITY
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-CHANGE-THIS')
# Allowed hosts
ALLOWED_HOSTS = [
    '.onrender.com',
    'localhost',
    '127.0.0.1',
]
# Database (PostgreSQL from Neon.tech)
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
# Static files (WhiteNoise)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Media files
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
]
# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
