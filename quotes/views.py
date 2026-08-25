from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .forms import QuoteRequestForm
from .models import QuoteRequest


def send_quote_emails(request, quote):
    file_url = ""
    if quote.uploaded_file:
        file_url = request.build_absolute_uri(quote.uploaded_file.url)

    context = {
        "quote": quote,
        "file_url": file_url,
        "site_name": "SenPrintTech",
    }

    admin_text = render_to_string("quotes/emails/admin_quote_request.txt", context)
    admin_html = render_to_string("quotes/emails/admin_quote_request.html", context)
    admin_email = EmailMultiAlternatives(
        subject=f"Nouvelle demande de devis - {quote.company_name}",
        body=admin_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.QUOTE_ADMIN_EMAIL],
        reply_to=[quote.email],
    )
    admin_email.attach_alternative(admin_html, "text/html")
    admin_email.send(fail_silently=False)

    client_text = render_to_string("quotes/emails/client_quote_confirmation.txt", context)
    client_html = render_to_string("quotes/emails/client_quote_confirmation.html", context)
    client_email = EmailMultiAlternatives(
        subject="Votre demande de devis SenPrintTech a bien été reçue",
        body=client_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[quote.email],
    )
    client_email.attach_alternative(client_html, "text/html")
    client_email.send(fail_silently=False)


def enterprise_quote(request):
    if request.method == "POST":
        form = QuoteRequestForm(request.POST, request.FILES)
        if form.is_valid():
            quote = form.save(commit=False)
            if request.user.is_authenticated:
                quote.user = request.user
            quote.save()
            try:
                send_quote_emails(request, quote)
                messages.success(request, "Votre demande de devis a bien été envoyée. Un email de confirmation vous a été adressé.")
            except Exception:
                messages.warning(
                    request,
                    "Votre demande de devis est bien enregistrée. L'email automatique n'a pas pu être envoyé pour le moment.",
                )
            return redirect("quotes:enterprise_quote")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "contact_name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
            }
        form = QuoteRequestForm(initial=initial)

    return render(request, "quotes/enterprise_quote.html", {"form": form})


@login_required(login_url="accounts:login")
def my_quotes(request):
    quotes = request.user.quote_requests.all()
    return render(request, "quotes/my_quotes.html", {"quotes": quotes})


@login_required(login_url="accounts:login")
def quote_detail(request, quote_id):
    quote = get_object_or_404(QuoteRequest, id=quote_id, user=request.user)
    return render(request, "quotes/quote_detail.html", {"quote": quote})
