from pathlib import Path

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.static import serve

from products.models import Product


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
    template_name = LEGAL_PAGES.get(page)
    if not template_name:
        raise Http404("Page not found")
    return render(request, template_name)


def media_file(request, path):
    media_root = Path(settings.MEDIA_ROOT)
    if (media_root / path).exists():
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    if path.startswith("products/"):
        bundled_media_root = settings.BASE_DIR / "mediafiles"
        if (bundled_media_root / path).exists():
            return serve(request, path, document_root=bundled_media_root)

    raise Http404("Media file not found")


@staff_member_required
def resync_product_images(request):
    """One-off: push the repo-bundled seed images into CLOUDINARY_URL storage.

    seed_senprintech only sets the image field's string path; it never
    uploads bytes, so switching to Cloudinary storage left every seeded
    product pointing at an asset that doesn't exist there yet.

    Cloudinary's storage backend assigns its own public_id on upload
    (it doesn't honor the requested name as-is), so the returned name
    from save() -- not the original path -- is what must be stored.
    """
    lines = []
    for product in Product.objects.exclude(image=""):
        original_name = product.image.name
        local_path = settings.BASE_DIR / "mediafiles" / original_name
        if not local_path.exists():
            lines.append(f"SKIP (no local file): {product.name} -> {original_name}")
            continue
        with open(local_path, "rb") as f:
            product.image.save(local_path.name, File(f), save=True)
        lines.append(f"UPLOADED: {product.name} -> {original_name} => {product.image.name}")
    return HttpResponse("\n".join(lines) or "No products with images found.", content_type="text/plain")
