from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Email backend console (print email ke terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Template debug mode
for template_setting in TEMPLATES:
    template_setting['OPTIONS']['debug'] = DEBUG