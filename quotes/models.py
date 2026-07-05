from django.conf import settings
from django.db import models

from ecommercesite.validators import validate_upload_file


class QuoteRequest(models.Model):
    NEW = "new"
    ANALYZING = "analyzing"
    SENT = "sent"
    ACCEPTED = "accepted"
    REFUSED = "refused"
    ARCHIVED = "archived"
    STATUS_CHOICES = [
        (NEW, "Nouveau"),
        (ANALYZING, "En analyse"),
        (SENT, "Devis envoye"),
        (ACCEPTED, "Accepte"),
        (REFUSED, "Refuse"),
        (ARCHIVED, "Archive"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="quote_requests",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    company_name = models.CharField(max_length=180)
    contact_name = models.CharField(max_length=180)
    email = models.EmailField()
    phone = models.CharField(max_length=60)
    product_type = models.CharField(max_length=120)
    desired_quantity = models.PositiveIntegerField()
    desired_deadline = models.CharField(max_length=120)
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    message = models.TextField()
    uploaded_file = models.FileField(
        upload_to="quote_uploads",
        blank=True,
        null=True,
        validators=[validate_upload_file],
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name} - {self.product_type}"


class ContactRequest(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    project_type = models.CharField(max_length=40)
    message = models.TextField()
    email_sent = models.BooleanField(default=False)
    email_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "demande contact"
        verbose_name_plural = "demandes contact"

    def __str__(self):
        return f"{self.name} - {self.email}"
