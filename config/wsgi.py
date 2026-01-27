"""
WSGI config for ppdb_system project.
"""
import os
from django.core.wsgi import get_wsgi_application
# Use production settings on Render
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings.production' if os.environ.get('RENDER') else 'config.settings.development'
)
application = get_wsgi_application()
