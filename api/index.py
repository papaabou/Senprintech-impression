"""Vercel entrypoint: exposes the Django WSGI app as ``app``.

Vercel's Python runtime statically scans this file for a top-level
``app``/``application``/``handler`` name, so it must be a plain
module-level assignment (not inside a try/except block).
"""

import os
import sys
import traceback

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommercesite.settings")


def _build_app():
    try:
        from django.core.wsgi import get_wsgi_application

        return get_wsgi_application()
    except Exception:
        boot_error = traceback.format_exc()
        debug_info = "PROJECT_ROOT=%r\nsys.path=%r\ncwd=%r\nlistdir(PROJECT_ROOT)=%r" % (
            PROJECT_ROOT,
            sys.path,
            os.getcwd(),
            os.listdir(PROJECT_ROOT) if os.path.isdir(PROJECT_ROOT) else "N/A",
        )
        body = (boot_error + "\n\n" + debug_info).encode("utf-8")

        def error_app(environ, start_response):
            start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
            return [body]

        return error_app


app = _build_app()
