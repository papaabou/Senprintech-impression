from django.db import models
from products.models import Product

from ecommercesite.validators import validate_upload_file


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    configured_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selected_options = models.JSONField(default=list, blank=True)
    uploaded_file = models.FileField(
        upload_to="client_uploads",
        blank=True,
        null=True,
        validators=[validate_upload_file],
    )

    def get_unit_price(self):
        return self.configured_price or self.product.get_base_price()
    
    def get_total_price(self):
        return self.get_unit_price() * self.quantity
    
