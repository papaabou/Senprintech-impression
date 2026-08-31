from django import forms

from .models import QuoteRequest


class QuoteRequestForm(forms.ModelForm):
    # Honeypot: invisible to real visitors (hidden via CSS), bots fill it in.
    # Not in Meta.fields, so ModelForm.save() never touches the model with it.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
        label="",
    )

    class Meta:
        model = QuoteRequest
        fields = [
            "company_name",
            "contact_name",
            "email",
            "phone",
            "product_type",
            "desired_quantity",
            "desired_deadline",
            "estimated_budget",
            "message",
            "uploaded_file",
        ]
        labels = {
            "company_name": "Nom entreprise",
            "contact_name": "Nom contact",
            "email": "Email",
            "phone": "Telephone",
            "product_type": "Type de produit",
            "desired_quantity": "Quantite souhaitee",
            "desired_deadline": "Délai souhaite",
            "estimated_budget": "Budget estime optionnel",
            "message": "Message",
            "uploaded_file": "Joindre un fichier (facultatif)",
        }
        widgets = {
            "company_name": forms.TextInput(attrs={"placeholder": "Nom de votre entreprise"}),
            "contact_name": forms.TextInput(attrs={"placeholder": "Votre nom"}),
            "email": forms.EmailInput(attrs={"placeholder": "contact@entreprise.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "+221 ..."}),
            "product_type": forms.Select(
                choices=[
                    ("Flyers", "Flyers"),
                    ("Cartes de visite", "Cartes de visite"),
                    ("T-shirts", "T-shirts"),
                    ("Mugs", "Mugs"),
                    ("Stickers", "Stickers"),
                    ("Packaging", "Packaging"),
                    ("Autre", "Autre"),
                ]
            ),
            "desired_quantity": forms.NumberInput(attrs={"placeholder": "Ex: 1000", "min": 1}),
            "desired_deadline": forms.TextInput(attrs={"placeholder": "Ex: sous 7 jours"}),
            "estimated_budget": forms.NumberInput(attrs={"placeholder": "Ex: 250000", "min": 0}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Detaillez le besoin, supports, formats, finitions..."}),
            "uploaded_file": forms.FileInput(attrs={"accept": ".pdf,.ai,.psd,.eps,.svg,.doc,.docx,.jpg,.jpeg,.png,.webp,.txt"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["uploaded_file"].required = False
        for name, field in self.fields.items():
            if name != "website":
                field.widget.attrs["class"] = "auth-input"

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            raise forms.ValidationError("Erreur de validation.")
        return value
