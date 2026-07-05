import time
from urllib.parse import quote

from django.conf import settings
from django.db.models import Sum

from cart.models import Cart

STATIC_VERSION = str(int(time.time()))


def static_version(request):
    if settings.DEBUG:
        return {"static_version": str(int(time.time()))}
    return {"static_version": STATIC_VERSION}


def whatsapp(request):
    message = settings.WHATSAPP_GENERAL_MESSAGE
    subject = settings.CONTACT_EMAIL_SUBJECT
    body = settings.CONTACT_EMAIL_BODY
    return {
        "WHATSAPP_NUMBER": settings.WHATSAPP_NUMBER,
        "WHATSAPP_DISPLAY_NUMBER": settings.WHATSAPP_DISPLAY_NUMBER,
        "WHATSAPP_GENERAL_MESSAGE": message,
        "WHATSAPP_GENERAL_URL": f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(message)}",
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "CONTACT_EMAIL_URL": f"mailto:{settings.CONTACT_EMAIL}?subject={quote(subject)}&body={quote(body)}",
    }


def cart_summary(request):
    cart_id = request.session.get("cart_id")
    if not cart_id:
        return {"cart_item_count": 0}

    count = (
        Cart.objects.filter(id=cart_id)
        .aggregate(total_quantity=Sum("items__quantity"))
        .get("total_quantity")
        or 0
    )
    return {"cart_item_count": count}
