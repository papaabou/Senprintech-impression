import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product, ProductOption

from .models import Cart, CartItem


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class CartFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.category = Category.objects.create(name="Impression", slug="impression")
        self.product = Product.objects.create(
            category=self.category,
            name="Flyers A5",
            slug="flyers-a5",
            price="10000.00",
            available=True,
        )
        self.text_option = ProductOption.objects.create(
            product=self.product,
            name="Texte personnalisé",
            code="texte",
            input_type=ProductOption.TEXT,
            required=True,
        )
        self.file_option = ProductOption.objects.create(
            product=self.product,
            name="Logo ou design",
            code="logo",
            input_type=ProductOption.FILE,
            required=True,
        )

    def test_add_update_and_remove_cart_item(self):
        add_response = self.client.post(
            reverse("cart:cart_add", args=[self.product.id]),
            {"cart_quantity": "2"},
        )

        self.assertEqual(add_response.status_code, 200)
        self.assertTrue(add_response.json()["success"])

        item = CartItem.objects.get()
        self.assertEqual(item.quantity, 2)

        detail_response = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Flyers A5")

        update_response = self.client.post(
            reverse("cart:update_item", args=[item.id]),
            {"quantity": "4"},
        )
        self.assertRedirects(update_response, reverse("cart:cart_detail"))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)

        remove_response = self.client.post(reverse("cart:remove_item", args=[item.id]))
        self.assertRedirects(remove_response, reverse("cart:cart_detail"))
        self.assertFalse(CartItem.objects.exists())

    def test_stale_cart_session_is_repaired_on_add(self):
        session = self.client.session
        session["cart_id"] = 999999
        session.save()

        response = self.client.post(
            reverse("cart:cart_add", args=[self.product.id]),
            {"cart_quantity": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_add_to_cart_without_required_text_or_file_options(self):
        response = self.client.post(
            reverse("cart:cart_add", args=[self.product.id]),
            {"cart_quantity": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        item = CartItem.objects.get()
        self.assertFalse(item.uploaded_file)
        self.assertEqual(item.selected_options, [])

        detail_response = self.client.get(reverse("cart:cart_detail"))
        self.assertContains(detail_response, "Aucun fichier fourni")

    def test_add_to_cart_with_optional_text_and_file_options(self):
        upload = SimpleUploadedFile(
            "logo.txt",
            b"logo test",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse("cart:cart_add", args=[self.product.id]),
            {
                "cart_quantity": "1",
                f"option_{self.text_option.id}": "Texte sur le flyer",
                f"option_{self.file_option.id}": upload,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        item = CartItem.objects.get()
        self.assertTrue(item.uploaded_file)
        self.assertEqual(len(item.selected_options), 2)
