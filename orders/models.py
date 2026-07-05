from django.conf import settings
from django.db import models

from ecommercesite.validators import validate_upload_file
from products.models import Product


class Order(models.Model):
    PENDING = "pending"
    FILE_RECEIVED = "file_received"
    REVIEWING = "reviewing"
    PRODUCTION = "production"
    READY = "ready"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    CLIENT_VALIDATION = "client_validation"
    PRINTING = "printing"
    FINISHING = "finishing"
    PACKAGING = "packaging"
    STATUS_CHOICES = [
        (PENDING, "En attente"),
        (FILE_RECEIVED, "Fichier recu"),
        (REVIEWING, "Verification fichier"),
        (CLIENT_VALIDATION, "Validation client"),
        (PRINTING, "Impression"),
        (FINISHING, "Finition"),
        (PACKAGING, "Emballage"),
        (SHIPPED, "Expedie"),
        (DELIVERED, "Livre"),
        (CANCELLED, "Annule"),
    ]
    PRIORITY_NORMAL = "normal"
    PRIORITY_URGENT = "urgent"
    PRIORITY_CHOICES = [
        (PRIORITY_NORMAL, "Normale"),
        (PRIORITY_URGENT, "Urgente"),
    ]
    PAYMENT_PENDING = "pending"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"
    PAYMENT_REFUNDED = "refunded"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, "En attente"),
        (PAYMENT_PAID, "Payé"),
        (PAYMENT_FAILED, "Refusé"),
        (PAYMENT_REFUNDED, "Remboursé"),
    ]
    PAYMENT_METHOD_WAVE = "wave"
    PAYMENT_METHOD_ORANGE_MONEY = "orange_money"
    PAYMENT_METHOD_CARD = "card"
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_WAVE, "Wave"),
        (PAYMENT_METHOD_ORANGE_MONEY, "Orange Money"),
        (PAYMENT_METHOD_CARD, "Carte bancaire (bientot)"),
    ]
    DELIVERY_PICKUP = "pickup"
    DELIVERY_DELIVERY = "delivery"
    DELIVERY_METHOD_CHOICES = [
        (DELIVERY_PICKUP, "Retrait"),
        (DELIVERY_DELIVERY, "Livraison"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    order_number = models.CharField(max_length=20, unique=True, blank=True, null=True, editable=False)
    full_name = models.CharField(max_length=250)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=120, blank=True)
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHOD_CHOICES,
        default=DELIVERY_PICKUP,
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=PENDING)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    production_deadline = models.DateField(blank=True, null=True)
    internal_notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assigned_orders",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    proof_file = models.FileField(
        upload_to="order_proofs",
        blank=True,
        null=True,
        validators=[validate_upload_file],
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING,
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_WAVE,
    )
    payment_provider = models.CharField(max_length=40, blank=True)
    payment_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def build_order_number(self):
        year = self.created_at.year if self.created_at else 2026
        return f"SPT-{year}-{self.pk:06d}"

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = (
                type(self).objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
        self.paid = self.payment_status == self.PAYMENT_PAID
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "payment_status" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"paid"}
        super().save(*args, **kwargs)
        if not self.order_number:
            self.order_number = self.build_order_number()
            type(self).objects.filter(pk=self.pk, order_number__isnull=True).update(
                order_number=self.order_number
            )
        if previous_status is None:
            OrderStatusHistory.objects.create(order=self, previous_status="", new_status=self.status)
        elif previous_status != self.status:
            OrderStatusHistory.objects.create(
                order=self,
                previous_status=previous_status,
                new_status=self.status,
            )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    selected_options = models.JSONField(default=list, blank=True)
    uploaded_file = models.FileField(
        upload_to="order_uploads",
        blank=True,
        null=True,
        validators=[validate_upload_file],
    )

    def get_unit_price(self):
        return self.price

    def get_cost(self):
        return self.get_unit_price() * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name="status_history", on_delete=models.CASCADE)
    previous_status = models.CharField(max_length=30, blank=True, choices=Order.STATUS_CHOICES)
    new_status = models.CharField(max_length=30, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Historique statut"
        verbose_name_plural = "Historiques statut"

    def __str__(self):
        return f"Commande #{self.order_id}: {self.previous_status or '-'} -> {self.new_status}"
