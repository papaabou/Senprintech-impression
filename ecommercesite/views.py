from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.static import serve


LEGAL_PAGES = {
    "privacy": "legal/privacy.html",
    "terms": "legal/terms.html",
    "sales": "legal/sales.html",
    "delivery": "legal/delivery.html",
    "returns": "legal/returns.html",
    "legal_notice": "legal/legal_notice.html",
    "faq": "legal/faq.html",
}


def legal_page(request, page):
    return render(request, LEGAL_PAGES[page])


def media_file(request, path):
    media_root = Path(settings.MEDIA_ROOT)
    if (media_root / path).exists():
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    if path.startswith("products/"):
        bundled_media_root = settings.BASE_DIR / "mediafiles"
        if (bundled_media_root / path).exists():
            return serve(request, path, document_root=bundled_media_root)

    raise Http404("Media file not found")
