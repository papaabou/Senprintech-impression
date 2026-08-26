from django import forms

from .models import Order


class OrderCreateForm(forms.ModelForm):
    def clean_payment_method(self):
        payment_method = self.cleaned_data["payment_method"]
        if payment_method == Order.PAYMENT_METHOD_CARD:
            raise forms.ValidationError("Le paiement par carte bancaire sera disponible prochainement.")
        return payment_method

    class Meta:
        model = Order
        fields = [
            "full_name",
            "phone",
            "email",
            "address",
            "city",
            "delivery_method",
            "payment_method",
            "notes",
        ]
        labels = {
            "full_name": "Nom complet",
            "phone": "Telephone",
            "email": "Email",
            "address": "Adresse",
            "city": "Ville",
            "delivery_method": "Mode de livraison",
            "payment_method": "Méthode de paiement",
            "notes": "Notes commande",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Votre nom complet"}),
            "phone": forms.TextInput(attrs={"placeholder": "+221 ..."}),
            "email": forms.EmailInput(attrs={"placeholder": "votre@email.com"}),
            "address": forms.TextInput(attrs={"placeholder": "Adresse de retrait/livraison"}),
            "city": forms.TextInput(attrs={"placeholder": "Dakar, Thies..."}),
            "payment_method": forms.RadioSelect(),
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Délai souhaite, details livraison, precision sur les fichiers...",
                }
            ),
        }
