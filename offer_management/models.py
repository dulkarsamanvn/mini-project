from django.db import models
from django.utils.timezone import now,make_aware,localtime
from category.models import  Category
from product.models import  Product

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        """Check if the coupon is currently valid."""
        return self.is_active and self.valid_from <= now() <= self.valid_until


# -------------------------------------------------------------------------------------

class Offer(models.Model):
    TYPE_CHOICES = [
        ('category', 'Category'),
        ('product', 'Product'),  # Changed to apply to product
    ]

    name = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField()
    offer_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    end_date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)  # Linked to Product instead of ProductVariant

    def __str__(self):
        return self.name

    def is_valid(self):
        """Check if the offer is still valid."""
        from django.utils import timezone

        return self.end_date >= timezone.now().date()