from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse


class InitialSuperuserCommandTests(TestCase):
    def test_creates_admin_when_no_superuser_exists(self):
        User = get_user_model()

        with patch.dict(
            "os.environ",
            {
                "ADMIN_USERNAME": "admin",
                "ADMIN_EMAIL": "admin@senprintech.com",
                "ADMIN_PASSWORD": "strong-test-password-123",
            },
        ):
            call_command("create_initial_superuser", stdout=StringIO())

        admin = User.objects.get(username="admin")
        self.assertEqual(admin.email, "admin@senprintech.com")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("strong-test-password-123"))

    def test_skips_when_superuser_already_exists(self):
        User = get_user_model()
        existing = User.objects.create_superuser(
            username="existing",
            email="existing@example.com",
            password="existing-password-123",
        )

        with patch.dict(
            "os.environ",
            {
                "ADMIN_USERNAME": "admin",
                "ADMIN_EMAIL": "admin@senprintech.com",
                "ADMIN_PASSWORD": "strong-test-password-123",
            },
        ):
            call_command("create_initial_superuser", stdout=StringIO())

        self.assertEqual(User.objects.filter(is_superuser=True).count(), 1)
        existing.refresh_from_db()
        self.assertTrue(existing.check_password("existing-password-123"))


class CustomerRegistrationTests(TestCase):
    @override_settings(ACCOUNT_EMAIL_VERIFICATION_REQUIRED=False, SECURE_SSL_REDIRECT=False)
    def test_registration_can_activate_and_login_without_email_verification(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "client-render",
                "first_name": "Client",
                "last_name": "Render",
                "email": "client-render@example.com",
                "password1": "strong-client-password-123",
                "password2": "strong-client-password-123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("accounts:account_home"))
        user = get_user_model().objects.get(username="client-render")
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)
