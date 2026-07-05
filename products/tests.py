from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from cart.models import CartItem
from products.forms import ProductConfigurationForm
from products.models import Product
from quotes.models import ContactRequest


class ProductPricingTests(TestCase):
    PRODUCT_SLUGS = [
        "cartes-de-visite",
        "flyers",
        "t-shirts-personnalises",
        "mugs-personnalises",
        "stickers",
        "roll-up",
    ]

    @classmethod
    def setUpTestData(cls):
        call_command("seed_senprintech", verbosity=0)

    def test_seeded_products_have_non_zero_base_prices(self):
        for slug in self.PRODUCT_SLUGS:
            with self.subTest(slug=slug):
                product = Product.objects.get(slug=slug)
                self.assertGreater(product.get_base_price(), 0)

    def test_configured_price_uses_base_price_and_option_deltas(self):
        product = Product.objects.get(slug="t-shirts-personnalises")
        selected_data = {}
        expected = Decimal(str(product.get_base_price()))

        for option in product.options.all():
            field_name = ProductConfigurationForm.get_field_name(option)
            if option.input_type == option.SELECT:
                choice = option.choices.order_by("-price_delta", "id").first()
                selected_data[field_name] = str(choice.id)
                expected += choice.price_delta

        form = ProductConfigurationForm(data=selected_data, product=product)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_configured_price(), expected)

    def test_cart_item_falls_back_to_safe_product_price(self):
        product = Product.objects.get(slug="mugs-personnalises")
        product.price = 0
        product.save(update_fields=["price"])

        item = CartItem(product=product, configured_price=0, quantity=3)

        self.assertEqual(item.get_unit_price(), product.get_base_price())
        self.assertEqual(item.get_total_price(), product.get_base_price() * 3)


class ContactRequestTests(TestCase):
    def contact_payload(self):
        return {
            "name": "Lamine",
            "email": "lamine@example.com",
            "phone": "777777777",
            "project_type": "flyers",
            "message": "Je veux vos produits",
        }

    @override_settings(SECURE_SSL_REDIRECT=False)
    @patch("products.views.send_contact_emails")
    def test_contact_request_is_saved_when_email_succeeds(self, send_contact_emails):
        response = self.client.post(reverse("products:contact_submit"), self.contact_payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"{reverse('products:product_list')}#contact")
        contact_request = ContactRequest.objects.get()
        self.assertEqual(contact_request.email, "lamine@example.com")
        self.assertTrue(contact_request.email_sent)
        send_contact_emails.assert_called_once()

    @override_settings(SECURE_SSL_REDIRECT=False)
    @patch("products.views.send_contact_emails", side_effect=RuntimeError("smtp down"))
    def test_contact_request_is_saved_when_email_fails(self, send_contact_emails):
        response = self.client.post(reverse("products:contact_submit"), self.contact_payload())

        self.assertEqual(response.status_code, 302)
        contact_request = ContactRequest.objects.get()
        self.assertFalse(contact_request.email_sent)
        self.assertIn("smtp down", contact_request.email_error)
        send_contact_emails.assert_called_once()
