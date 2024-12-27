from django.db import models
from django.conf import settings
from product.models import Product,ProductVariant
# Create your models here.
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Reference to your custom user model
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Reference to Product model
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)  # Optional variant
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when added to wishlist

    class Meta:
        unique_together = ('user', 'product')  # Ensure unique user-product combination
        ordering = ['-created_at']  # Optional: Latest items first

    def __str__(self):
        return f"{self.user} - {self.product.name}"
    
    def get_variant(self):
        """Fetch the chosen variant or return the primary variant."""
        return self.variant if self.variant else self.product.variants.first()