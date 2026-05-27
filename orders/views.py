from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from cart.models import Cart

from .forms import OrderCreateForm
from .models import Order, OrderItem


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
