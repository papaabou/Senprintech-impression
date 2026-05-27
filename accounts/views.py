import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from orders.models import Order
from quotes.models import QuoteRequest

from .forms import CustomerLoginForm, CustomerRegistrationForm, EmailVerificationForm
from .models import EmailVerificationCode


logger = logging.getLogger(__name__)


def send_verification_email(request, user, code):
    verify_url = request.build_absolute_uri(reverse("accounts:verify_email"))
    context = {
        "user": user,
        "code": code,
        "verify_url": verify_url,
        "expires_minutes": EmailVerificationCode.EXPIRES_MINUTES,
        "site_name": "SenPrinTech",
    }
    text_body = render_to_string("accounts/emails/verify_email.txt", context)
    html_body = render_to_string("accounts/emails/verify_email.html", context)
    email = EmailMultiAlternatives(
        subject="Confirmez votre compte SenPrinTech",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def set_pending_verification(request, user):
    request.session["pending_verification_user_id"] = user.id


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:account_home")

    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.is_active = not settings.ACCOUNT_EMAIL_VERIFICATION_REQUIRED
            user.save()

            if not settings.ACCOUNT_EMAIL_VERIFICATION_REQUIRED:
                login(request, user)
                messages.success(request, "Votre compte a été créé. Vous êtes connecté.")
                return redirect("accounts:account_home")

            verification, code = EmailVerificationCode.create_for_user(user)
            set_pending_verification(request, user)
            try:
                send_verification_email(request, user, code)
                messages.success(
                    request,
                    "Votre compte a été créé. Entrez le code reçu par email pour l'activer.",
                )
            except Exception:
                logger.exception("Unable to send account verification email for user_id=%s", user.id)
                messages.warning(
                    request,
                    "Votre compte a été créé, mais l'email de vérification n'a pas pu être envoyé. Demandez un nouveau code.",
                )
            return redirect("accounts:verify_email")
    else:
        form = CustomerRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:account_home")

    if request.method == "POST":
        form = CustomerLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Connexion réussie.")
            return redirect(request.GET.get("next") or "accounts:account_home")
        inactive_user = getattr(form, "inactive_user", None)
        if inactive_user:
            set_pending_verification(request, inactive_user)
            messages.warning(request, "Veuillez confirmer votre adresse email avant de vous connecter.")
            return redirect("accounts:verify_email")
    else:
        form = CustomerLoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect("products:product_list")


def verify_email(request):
    user_id = request.session.get("pending_verification_user_id")
    if not user_id:
        messages.warning(request, "Inscrivez-vous ou connectez-vous pour vérifier votre adresse email.")
        return redirect("accounts:login")

    user = get_object_or_404(User, id=user_id)
    if user.is_active:
        request.session.pop("pending_verification_user_id", None)
        messages.success(request, "Votre email est déjà confirmé. Vous pouvez vous connecter.")
        return redirect("accounts:login")

    verification, code = EmailVerificationCode.create_for_user(user) if not hasattr(user, "email_verification") else (user.email_verification, None)

    if request.method == "POST":
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            is_valid, error = verification.verify(form.cleaned_data["code"])
            if is_valid:
                user.is_active = True
                user.save(update_fields=["is_active"])
                request.session.pop("pending_verification_user_id", None)
                messages.success(request, "Votre email a été confirmé, vous pouvez maintenant vous connecter.")
                return redirect("accounts:login")
            messages.error(request, error)
    else:
        form = EmailVerificationForm()

    return render(request, "accounts/verify_email.html", {"form": form, "user_email": user.email, "verification": verification})


def resend_verification_code(request):
    user_id = request.session.get("pending_verification_user_id")
    if not user_id:
        messages.success(request, "Si une vérification est nécessaire, un nouveau code sera envoyé.")
        return redirect("accounts:login")

    user = get_object_or_404(User, id=user_id)
    if user.is_active:
        request.session.pop("pending_verification_user_id", None)
        messages.success(request, "Votre email est déjà confirmé. Vous pouvez vous connecter.")
        return redirect("accounts:login")

    verification, _ = EmailVerificationCode.objects.get_or_create(
        user=user,
        defaults={
            "code_hash": "",
            "expires_at": timezone.now(),
        },
    )
    can_resend, reason = verification.can_resend()
    if not can_resend:
        messages.warning(request, reason)
        return redirect("accounts:verify_email")

    code = verification.resend()
    try:
        send_verification_email(request, user, code)
        messages.success(request, "Un nouveau code de vérification vous a été envoyé.")
    except Exception:
        logger.exception("Unable to resend account verification email for user_id=%s", user.id)
        messages.warning(request, "Le code a été généré, mais l'email n'a pas pu être envoyé pour le moment.")
    return redirect("accounts:verify_email")


@login_required(login_url="accounts:login")
def account_home(request):
    recent_orders = request.user.orders.prefetch_related("items__product").order_by("-created_at")[:3]
    recent_quotes = request.user.quote_requests.order_by("-created_at")[:3]
    return render(
        request,
        "accounts/account_home.html",
        {"recent_orders": recent_orders, "recent_quotes": recent_quotes},
    )


@login_required(login_url="accounts:login")
def order_list(request):
    orders = request.user.orders.prefetch_related("items__product").order_by("-created_at")
    return render(request, "accounts/order_list.html", {"orders": orders})


@login_required(login_url="accounts:login")
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        id=order_id,
        user=request.user,
    )
    return render(request, "accounts/order_detail.html", {"order": order})


@login_required(login_url="accounts:login")
def quote_list(request):
    quotes = request.user.quote_requests.order_by("-created_at")
    return render(request, "quotes/my_quotes.html", {"quotes": quotes})


@login_required(login_url="accounts:login")
def quote_detail(request, quote_id):
    quote = get_object_or_404(QuoteRequest, id=quote_id, user=request.user)
    return render(request, "quotes/quote_detail.html", {"quote": quote})
