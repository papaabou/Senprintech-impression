from django.db import models
from django.urls import reverse


DEFAULT_PRODUCT_PRICES = {
    "cartes-de-visite": 5000,
    "flyers": 8000,
    "roll-up": 25000,
    "t-shirts-personnalises": 10000,
    "mugs-personnalises": 7000,
    "stickers": 3000,
    "brochures-depliants": 12000,
    "enveloppes-papier-entete": 6000,
}


class Category(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(unique=True)
    
    class Meta:
        verbose_name_plural = "categories"
    
    def __str__(self):
        return self.name
    

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products', blank=True, null=True)
    
    def __str__(self) -> str:
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'id':self.id, 'slug':self.slug})

    def get_base_price(self):
        if self.price and self.price > 0:
            return self.price
        return DEFAULT_PRODUCT_PRICES.get(self.slug, 0)


class ProductOption(models.Model):
    SELECT = "select"
    TEXT = "text"
    FILE = "file"
    INPUT_TYPE_CHOICES = [
        (SELECT, "Liste de choix"),
        (TEXT, "Texte libre"),
        (FILE, "Upload fichier"),
    ]

    product = models.ForeignKey(Product, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=80)
    input_type = models.CharField(max_length=20, choices=INPUT_TYPE_CHOICES, default=SELECT)
    required = models.BooleanField(default=True)
    help_text = models.CharField(max_length=250, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("product", "code")

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductOptionChoice(models.Model):
    option = models.ForeignKey(ProductOption, related_name="choices", on_delete=models.CASCADE)
    label = models.CharField(max_length=120)
    value = models.SlugField(max_length=80)
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("option", "value")

    def __str__(self):
        return f"{self.option.name}: {self.label}"


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
