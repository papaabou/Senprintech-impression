from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from cart.models import CartItem
from products.forms import ProductConfigurationForm
from products.models import Product


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
