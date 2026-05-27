import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import Case, IntegerField, Value, When
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse

from .forms import ContactForm, ProductConfigurationForm
from .models import Category, ContactRequest, Product


logger = logging.getLogger(__name__)


def get_catalog_context(category_slug=None, contact_form=None):
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
        "contact_form": contact_form or ContactForm(),
    }


def product_list(request, category_slug=None):
    return render(request, 'products/product/list.html', get_catalog_context(category_slug))


def product_detail(request, id, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("options__choices"),
        id=id,
        slug=slug,
        available=True,
    )
    configuration_form = ProductConfigurationForm(product=product)
    whatsapp_message = (
        f"Bonjour SenPrinTech, je suis interesse par ce produit : {product.name}. "
        "Pouvez-vous me conseiller ?"
    )
    return render(
        request,
        'products/product/detail.html',
        {
            'product': product,
            "configuration_form": configuration_form,
            "product_whatsapp_url": f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(whatsapp_message)}",
        },
    )


def send_contact_emails(form):
    data = form.cleaned_data
    context = {
        "contact": data,
        "project_type_label": dict(form.fields["project_type"].choices).get(data["project_type"], data["project_type"]),
        "site_name": "SenPrinTech",
    }

    admin_text = render_to_string("products/emails/admin_contact_request.txt", context)
    admin_html = render_to_string("products/emails/admin_contact_request.html", context)
    admin_email = EmailMultiAlternatives(
        subject=f"Nouveau message contact - {data['name']}",
        body=admin_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.QUOTE_ADMIN_EMAIL],
        reply_to=[data["email"]],
    )
    admin_email.attach_alternative(admin_html, "text/html")
    admin_email.send(fail_silently=False)

    client_text = render_to_string("products/emails/client_contact_confirmation.txt", context)
    client_html = render_to_string("products/emails/client_contact_confirmation.html", context)
    client_email = EmailMultiAlternatives(
        subject="Votre message SenPrinTech a bien été reçu",
        body=client_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[data["email"]],
    )
    client_email.attach_alternative(client_html, "text/html")
    client_email.send(fail_silently=False)


def contact_submit(request):
    if request.method != "POST":
        return redirect("products:product_list")

    form = ContactForm(request.POST)
    if form.is_valid():
        contact_request = ContactRequest.objects.create(**form.cleaned_data)
        try:
            send_contact_emails(form)
            contact_request.email_sent = True
            contact_request.save(update_fields=["email_sent"])
            messages.success(
                request,
                "Votre message a bien été envoyé. Un email de confirmation vous a été adressé.",
            )
        except Exception as exc:
            logger.exception("Unable to send contact email for contact_request_id=%s", contact_request.id)
            contact_request.email_error = str(exc)
            contact_request.save(update_fields=["email_error"])
            messages.warning(
                request,
                "Votre message est bien reçu, mais l'email automatique n'a pas pu être envoyé pour le moment.",
            )
        return HttpResponseRedirect(f"{reverse('products:product_list')}#contact")

    messages.error(request, "Veuillez corriger les champs du formulaire de contact.")
    return render(request, "products/product/list.html", get_catalog_context(contact_form=form))
