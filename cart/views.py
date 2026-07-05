from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from products.forms import ProductConfigurationForm
from products.models import Product
from .models import Cart, CartItem
from django.views.decorators.http import require_POST
from django.http import JsonResponse


def get_session_cart(request):
    cart_id = request.session.get("cart_id")
    if not cart_id:
        return None

    try:
        return Cart.objects.prefetch_related("items__product").get(id=cart_id)
    except Cart.DoesNotExist:
        request.session.pop("cart_id", None)
        return None


@require_POST
def cart_add(request, product_id):
    cart_id = request.session.get('cart_id')
    
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
    
    product = get_object_or_404(
        Product.objects.prefetch_related("options__choices"),
        id=product_id,
        available=True,
    )
    form = ProductConfigurationForm(request.POST, request.FILES, product=product)

    if not form.is_valid():
        return JsonResponse(
            {
                "success": False,
                "message": "Veuillez verifier les options du produit.",
                "errors": form.errors,
            },
            status=400,
        )

    try:
        line_quantity = int(request.POST.get("cart_quantity", 1))
    except (TypeError, ValueError):
        line_quantity = 1

    if line_quantity < 1 or line_quantity > 99:
        return JsonResponse(
            {
                "success": False,
                "message": "La quantite panier doit etre comprise entre 1 et 99.",
            },
            status=400,
        )

    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=line_quantity,
        configured_price=form.get_configured_price(),
        selected_options=form.get_selected_options(),
        uploaded_file=form.get_uploaded_file(),
    )
    
    cart_item_count = (
        CartItem.objects.filter(cart=cart).aggregate(total=Sum("quantity")).get("total") or 0
    )

    response_data = {
        "success":True,
        "message": f'Added {product.name} to cart',
        "cart_item_id": cart_item.id,
        "configured_price": str(cart_item.configured_price),
        "quantity": cart_item.quantity,
        "line_total": str(cart_item.get_total_price()),
        "cart_item_count": cart_item_count,
    }

    return JsonResponse(response_data)
    
    
def cart_detail(request):
    cart = get_session_cart(request)
    if not cart or not cart.items.exists():
        cart=None
    
    return render(request, "cart/detail.html", {"cart":cart})
    

@require_POST
def cart_update(request, item_id):
    cart = get_session_cart(request)
    if not cart:
        return redirect("cart:cart_detail")

    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    try:
        quantity = int(request.POST.get("quantity", item.quantity))
    except (TypeError, ValueError):
        quantity = item.quantity

    if quantity < 1:
        item.delete()
    else:
        item.quantity = min(quantity, 99)
        item.save(update_fields=["quantity"])

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, item_id):
    cart = get_session_cart(request)
    if not cart:
        return redirect("cart:cart_detail")

    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    
    return redirect("cart:cart_detail")

    
