"""Vercel entrypoint: exposes the Django WSGI app as ``app``.

Vercel's Python runtime auto-detects a module-level ``app`` variable
that is a WSGI callable and routes requests to it directly.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommercesite.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
