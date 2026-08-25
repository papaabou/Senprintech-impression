import shutil
import tempfile

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from cart.models import Cart, CartItem
from products.models import Category, Product

from .views import build_order_whatsapp_url
from .models import Order


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class AssistedPaymentCheckoutTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="client",
            email="client@example.com",
            password="test-pass-123",
        )
        self.category = Category.objects.create(name="Impression", slug="impression")
        self.product = Product.objects.create(
            category=self.category,
            name="Cartes de visite",
            slug="cartes-de-visite",
            price="15000.00",
        )

    def create_cart_session(self, uploaded_file=None):
        cart = Cart.objects.create()
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
            uploaded_file=uploaded_file,
        )
        session = self.client.session
        session["cart_id"] = cart.id
        session.save()
        return cart

    def checkout_payload(self, payment_method=Order.PAYMENT_METHOD_WAVE):
        return {
            "full_name": "Client Test",
            "phone": "+221770000000",
            "email": "client@example.com",
            "address": "Dakar Plateau",
            "city": "Dakar",
            "delivery_method": Order.DELIVERY_PICKUP,
            "payment_method": payment_method,
            "notes": "Besoin rapidement.",
        }

    def test_checkout_creates_pending_assisted_payment_order(self):
        self.client.force_login(self.user)
        self.create_cart_session()

        response = self.client.post(reverse("orders:order_create"), self.checkout_payload(), follow=True)

        order = Order.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [(reverse("orders:order_confirmation", args=[order.id]), 302)])
        self.assertContains(response, "Finaliser votre paiement")
        self.assertContains(response, "Payer sur WhatsApp")
        self.assertContains(response, "wa.me/221710353207")
        self.assertContains(response, order.order_number)
        self.assertContains(response, "Aucun fichier fourni")
        self.assertRegex(order.order_number, r"^SPT-\d{4}-\d{6}$")
        self.assertEqual(order.order_number, f"SPT-{order.created_at.year}-{order.id:06d}")
        self.assertEqual(order.payment_status, Order.PAYMENT_PENDING)
        self.assertEqual(order.payment_method, Order.PAYMENT_METHOD_WAVE)
        self.assertEqual(order.payment_provider, Order.PAYMENT_METHOD_WAVE)
        self.assertFalse(order.paid)
        self.assertEqual(order.items.count(), 1)
        self.assertNotIn("cart_id", self.client.session)

    def test_checkout_preserves_optional_uploaded_file(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            "logo.txt",
            b"logo test",
            content_type="text/plain",
        )
        self.create_cart_session(uploaded_file=upload)

        response = self.client.post(reverse("orders:order_create"), self.checkout_payload(), follow=True)

        order = Order.objects.get()
        item = order.items.get()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(item.uploaded_file)
        self.assertContains(response, "logo")

    def test_order_numbers_are_unique_and_used_in_whatsapp_message(self):
        first = Order.objects.create(
            user=self.user,
            full_name="Client Test",
            phone="+221770000000",
            email="client@example.com",
            address="Dakar Plateau",
            city="Dakar",
            payment_method=Order.PAYMENT_METHOD_WAVE,
        )
        second = Order.objects.create(
            user=self.user,
            full_name="Client Deux",
            phone="+221770000001",
            email="client2@example.com",
            address="Dakar",
            city="Dakar",
            payment_method=Order.PAYMENT_METHOD_ORANGE_MONEY,
        )

        self.assertNotEqual(first.order_number, second.order_number)
        self.assertEqual(first.order_number, f"SPT-{first.created_at.year}-{first.id:06d}")
        self.assertEqual(second.order_number, f"SPT-{second.created_at.year}-{second.id:06d}")
        self.assertIn(first.order_number, build_order_whatsapp_url(first))

    def test_admin_can_update_payment_status_and_client_sees_it(self):
        order_admin = admin.site._registry[Order]
        self.assertIn("payment_status", order_admin.list_display)
        self.assertIn("payment_status", order_admin.list_editable)
        self.assertIn("payment_status", order_admin.list_filter)
        self.assertNotIn("payment_status", order_admin.readonly_fields)
        self.assertIn("mark_payment_paid", order_admin.actions)

        order = Order.objects.create(
            user=self.user,
            full_name="Client Test",
            phone="+221770000000",
            email="client@example.com",
            address="Dakar Plateau",
            city="Dakar",
            payment_method=Order.PAYMENT_METHOD_WAVE,
        )

        order.payment_status = Order.PAYMENT_PAID
        order.save(update_fields=["payment_status"])
        order.refresh_from_db()

        self.assertEqual(order.payment_status, Order.PAYMENT_PAID)
        self.assertTrue(order.paid)

        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:order_detail", args=[order.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payé")

    def test_card_payment_method_is_not_available_yet(self):
        self.client.force_login(self.user)
        self.create_cart_session()

        response = self.client.post(
            reverse("orders:order_create"),
            self.checkout_payload(payment_method=Order.PAYMENT_METHOD_CARD),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Le paiement par carte bancaire sera disponible prochainement.")
        self.assertFalse(Order.objects.exists())
