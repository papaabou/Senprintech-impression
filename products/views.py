from urllib.parse import quote

from django.conf import settings
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404, render

from .forms import ProductConfigurationForm
from .models import Category, Product


def get_catalog_context(category_slug=None):
    category = None
    product_order = [
        "cartes-de-visite",
        "flyers",
        "roll-up",
        "t-shirts-personnalises",
        "mugs-personnalises",
        "stickers",
        "brochures-depliants",
        "enveloppes-papier-entete",
    ]
    ordering = Case(
        *[When(slug=slug, then=Value(index)) for index, slug in enumerate(product_order)],
        default=Value(len(product_order)),
        output_field=IntegerField(),
    )
    products = (
        Product.objects.filter(available=True)
        .select_related("category")
        .annotate(catalog_order=ordering)
        .order_by("catalog_order", "name")
    )
    categories = (
        Category.objects.filter(products__available=True)
        .distinct()
        .order_by("name")
    )
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return {
        "category": category,
        "products": products,
        "categories": categories,
    }


def product_list(request, category_slug=None):
    return render(request, "products/product/list.html", get_catalog_context(category_slug))


def product_detail(request, id, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("options__choices"),
        id=id,
        slug=slug,
        available=True,
    )
    configuration_form = ProductConfigurationForm(product=product)
    whatsapp_message = (
        f"Bonjour SenPrintTech, je suis interesse par ce produit : {product.name}. "
        "Pouvez-vous me conseiller ?"
    )
    return render(
        request,
        "products/product/detail.html",
        {
            "product": product,
            "configuration_form": configuration_form,
            "product_whatsapp_url": f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(whatsapp_message)}",
        },
    )
