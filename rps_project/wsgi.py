"""
WSGI config for rps_project project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rps_project.settings')

application = get_wsgi_application()
