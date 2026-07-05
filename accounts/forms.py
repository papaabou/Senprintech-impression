from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CustomerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Prenom", max_length=150, required=False)
    last_name = forms.CharField(label="Nom", max_length=150, required=False)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "ex: senprintech",
            "first_name": "Votre prenom",
            "last_name": "Votre nom",
            "email": "votre@email.com",
            "password1": "Mot de passe",
            "password2": "Confirmer le mot de passe",
        }
        labels = {
            "username": "Nom d'utilisateur",
            "password1": "Mot de passe",
            "password2": "Confirmation",
        }
        for name, field in self.fields.items():
            field.label = labels.get(name, field.label)
            field.help_text = ""
            field.widget.attrs.update(
                {
                    "class": "auth-input",
                    "placeholder": placeholders.get(name, ""),
                }
            )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        existing = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError("Un utilisateur avec ce nom existe déjà.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError("Un compte existe déjà avec cette adresse email.")
        return email


class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(label="Email ou nom d'utilisateur")

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "auth-input", "placeholder": "Email ou nom d'utilisateur"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "auth-input", "placeholder": "Votre mot de passe"}
        )

    def clean(self):
        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email and password:
            username = username_or_email
            if "@" in username_or_email:
                user = User.objects.filter(email__iexact=username_or_email).first()
                if user:
                    username = user.get_username()

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                inactive_user = None
                lookup = {"username__iexact": username_or_email}
                if "@" in username_or_email:
                    lookup = {"email__iexact": username_or_email}
                candidate = User.objects.filter(**lookup).first()
                if candidate and not candidate.is_active and candidate.check_password(password):
                    inactive_user = candidate
                self.inactive_user = inactive_user
                raise ValidationError(
                    "Identifiants incorrects. Vérifiez votre email, nom d'utilisateur ou mot de passe.",
                    code="invalid_login",
                )
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class EmailVerificationForm(forms.Form):
    code = forms.CharField(
        label="Code de vérification",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "auth-input verification-code-input",
                "placeholder": "000000",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("Le code doit contenir uniquement des chiffres.")
        return code
