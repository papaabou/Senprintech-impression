"""Vercel entrypoint: exposes the Django WSGI app as ``app``.

Vercel's Python runtime auto-detects a module-level ``app`` variable
that is a WSGI callable and routes requests to it directly.
"""

import os
import sys
import traceback

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommercesite.settings")

try:
    from django.core.wsgi import get_wsgi_application

    app = get_wsgi_application()
except Exception:
    _boot_error = traceback.format_exc()
    _debug_info = "PROJECT_ROOT=%r\nsys.path=%r\ncwd=%r\nlistdir(PROJECT_ROOT)=%r" % (
        PROJECT_ROOT,
        sys.path,
        os.getcwd(),
        os.listdir(PROJECT_ROOT) if os.path.isdir(PROJECT_ROOT) else "N/A",
    )

    def app(environ, start_response):
        body = (_boot_error + "\n\n" + _debug_info).encode("utf-8")
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [body]
