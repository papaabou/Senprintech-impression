import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from cart.models import Cart

from .forms import OrderCreateForm
from .models import Order, OrderItem


logger = logging.getLogger(__name__)


def build_order_whatsapp_url(order):
    lines = [
        "Bonjour SenPrinTech,",
        f"Je souhaite finaliser le paiement de la commande {order.order_number}",
        "",
        f"Nom : {order.full_name}",
        f"Montant : {order.get_total_cost()} FCFA",
        f"Methode choisie : {order.get_payment_method_display()}",
    ]
    message = "\n".join(lines)
    return f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(message)}"


def send_order_emails(request, order):
    items = [
        {
            "item": item,
            "file_url": request.build_absolute_uri(item.uploaded_file.url) if item.uploaded_file else "",
        }
        for item in order.items.select_related("product").all()
    ]
    admin_url = request.build_absolute_uri(
        reverse("admin:orders_order_change", args=[order.id])
    )
    context = {"order": order, "items": items, "admin_url": admin_url}

    admin_text = render_to_string("orders/emails/admin_order_notification.txt", context)
    admin_html = render_to_string("orders/emails/admin_order_notification.html", context)
    admin_email = EmailMultiAlternatives(
        subject=f"Nouvelle commande {order.order_number}",
        body=admin_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.QUOTE_ADMIN_EMAIL],
        reply_to=[order.email],
    )
    admin_email.attach_alternative(admin_html, "text/html")
    admin_email.send(fail_silently=False)

    client_text = render_to_string("orders/emails/client_order_confirmation.txt", context)
    client_html = render_to_string("orders/emails/client_order_confirmation.html", context)
    client_email = EmailMultiAlternatives(
        subject=f"Votre commande SenPrinTech {order.order_number} est confirmee",
        body=client_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    client_email.attach_alternative(client_html, "text/html")
    client_email.send(fail_silently=False)


@login_required(login_url="accounts:login")
def order_create(request):
    cart_id = request.session.get("cart_id")

    if not cart_id:
        return redirect("cart:cart_detail")

    cart = get_object_or_404(Cart, id=cart_id)
    if not cart.items.exists():
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.payment_status = Order.PAYMENT_PENDING
            order.payment_provider = order.payment_method
            order.save()

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.configured_price or item.product.get_base_price(),
                    quantity=item.quantity,
                    selected_options=item.selected_options,
                    uploaded_file=item.uploaded_file,
                )
            cart.delete()
            del request.session["cart_id"]

            try:
                send_order_emails(request, order)
            except Exception:
                logger.exception("Unable to send order notification emails for order_id=%s", order.id)
                messages.warning(
                    request,
                    "Votre commande est bien enregistree, mais l'email de confirmation n'a pas pu etre envoye.",
                )

            return redirect("orders:order_confirmation", order.id)

    else:
        initial = {
            "full_name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
        }
        form = OrderCreateForm(initial=initial)

    return render(request, "orders/order_create.html", {"cart": cart, "form": form})


@login_required(login_url="accounts:login")
def order_confirmation(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )
    return render(
        request,
        "orders/order_confirmation.html",
        {
            "order": order,
            "whatsapp_order_url": build_order_whatsapp_url(order),
        },
    )
