from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


class EmailVerificationCode(models.Model):
    CODE_LENGTH = 6
    EXPIRES_MINUTES = 15
    MAX_ATTEMPTS = 5
    MAX_RESENDS = 5
    RESEND_COOLDOWN_SECONDS = 60

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="email_verification",
        on_delete=models.CASCADE,
    )
    code_hash = models.CharField(max_length=256)
    attempts = models.PositiveIntegerField(default=0)
    resend_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "code de vérification email"
        verbose_name_plural = "codes de vérification email"

    def __str__(self):
        return f"Vérification email - {self.user.email or self.user.username}"

    @classmethod
    def generate_plain_code(cls):
        return get_random_string(cls.CODE_LENGTH, allowed_chars="0123456789")

    @classmethod
    def create_for_user(cls, user):
        plain_code = cls.generate_plain_code()
        verification, _ = cls.objects.update_or_create(
            user=user,
            defaults={
                "code_hash": make_password(plain_code),
                "attempts": 0,
                "resend_count": 0,
                "expires_at": timezone.now() + timedelta(minutes=cls.EXPIRES_MINUTES),
                "last_sent_at": timezone.now(),
                "verified_at": None,
            },
        )
        return verification, plain_code

    def can_resend(self):
        if self.resend_count >= self.MAX_RESENDS:
            return False, "Le nombre maximum de renvois est atteint. Contactez SenPrintTech si besoin."
        elapsed = timezone.now() - self.last_sent_at
        if elapsed.total_seconds() < self.RESEND_COOLDOWN_SECONDS:
            return False, "Veuillez patienter une minute avant de demander un nouveau code."
        return True, ""

    def resend(self):
        plain_code = self.generate_plain_code()
        self.code_hash = make_password(plain_code)
        self.attempts = 0
        self.resend_count += 1
        self.expires_at = timezone.now() + timedelta(minutes=self.EXPIRES_MINUTES)
        self.last_sent_at = timezone.now()
        self.verified_at = None
        self.save(
            update_fields=[
                "code_hash",
                "attempts",
                "resend_count",
                "expires_at",
                "last_sent_at",
                "verified_at",
                "updated_at",
            ]
        )
        return plain_code

    def is_expired(self):
        return timezone.now() > self.expires_at

    def verify(self, code):
        if self.verified_at:
            return False, "Ce compte est déjà vérifié."
        if self.is_expired():
            return False, "Ce code a expiré. Demandez un nouveau code."
        if self.attempts >= self.MAX_ATTEMPTS:
            return False, "Trop de tentatives. Demandez un nouveau code."

        self.attempts += 1
        self.save(update_fields=["attempts", "updated_at"])

        if not check_password(code, self.code_hash):
            return False, "Code incorrect. Vérifiez l'email reçu."

        self.verified_at = timezone.now()
        self.save(update_fields=["verified_at", "updated_at"])
        return True, ""
