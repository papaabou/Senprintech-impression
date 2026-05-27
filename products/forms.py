from decimal import Decimal

from django import forms

from .models import ProductOptionChoice


class ContactForm(forms.Form):
    name = forms.CharField(
        label="Nom complet",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Votre nom"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "votre@email.com"}),
    )
    phone = forms.CharField(
        label="Telephone",
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "+221 ..."}),
    )
    project_type = forms.ChoiceField(
        label="Type de projet",
        choices=[
            ("flyers", "Flyers"),
            ("business_cards", "Cartes de visite"),
            ("tshirts", "T-shirts"),
            ("mugs", "Mugs"),
            ("stickers", "Stickers"),
            ("business", "Impression entreprise"),
            ("other", "Autre demande"),
        ],
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(
            attrs={
                "placeholder": "Expliquez votre besoin, quantite, delai souhaite...",
                "rows": 5,
            }
        ),
    )


class ProductConfigurationForm(forms.Form):
    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.product_options = list(
            product.options.prefetch_related("choices").all()
        )

        for option in self.product_options:
            field_name = self.get_field_name(option)
            if option.input_type == option.SELECT:
                choices = []
                for choice in option.choices.all():
                    label = choice.label
                    if choice.price_delta:
                        label = f"{label} (+{choice.price_delta} FCFA)"
                    choices.append((str(choice.id), label))
                self.fields[field_name] = forms.ChoiceField(
                    label=option.name,
                    choices=choices,
                    required=option.required,
                    help_text=option.help_text,
                )
            elif option.input_type == option.TEXT:
                self.fields[field_name] = forms.CharField(
                    label=option.name,
                    required=False,
                    help_text=option.help_text,
                    widget=forms.Textarea(attrs={"rows": 3}),
                )
            elif option.input_type == option.FILE:
                self.fields[field_name] = forms.FileField(
                    label=option.name,
                    required=False,
                    help_text=option.help_text,
                )

    @staticmethod
    def get_field_name(option):
        return f"option_{option.id}"

    def get_selected_options(self):
        selected_options = []
        if not self.is_valid():
            return selected_options

        for option in self.product_options:
            field_name = self.get_field_name(option)
            value = self.cleaned_data.get(field_name)
            if option.input_type == option.SELECT and value:
                choice = ProductOptionChoice.objects.get(id=value, option=option)
                selected_options.append(
                    {
                        "option_id": option.id,
                        "name": option.name,
                        "code": option.code,
                        "type": option.input_type,
                        "choice_id": choice.id,
                        "label": choice.label,
                        "value": choice.value,
                        "price_delta": str(choice.price_delta),
                    }
                )
            elif option.input_type == option.TEXT and value:
                selected_options.append(
                    {
                        "option_id": option.id,
                        "name": option.name,
                        "code": option.code,
                        "type": option.input_type,
                        "value": value,
                        "price_delta": "0",
                    }
                )
            elif option.input_type == option.FILE and value:
                selected_options.append(
                    {
                        "option_id": option.id,
                        "name": option.name,
                        "code": option.code,
                        "type": option.input_type,
                        "value": value.name,
                        "price_delta": "0",
                    }
                )

        return selected_options

    def get_configured_price(self):
        total = Decimal(str(self.product.get_base_price()))
        for selected in self.get_selected_options():
            total += ProductOptionChoice.objects.filter(
                id=selected.get("choice_id")
            ).values_list("price_delta", flat=True).first() or 0
        return total

    def get_uploaded_file(self):
        if not self.is_valid():
            return None

        for option in self.product_options:
            if option.input_type == option.FILE:
                uploaded = self.cleaned_data.get(self.get_field_name(option))
                if uploaded:
                    return uploaded
        return None
