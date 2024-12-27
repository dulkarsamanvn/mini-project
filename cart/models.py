from django.db import models
from django.conf import settings
from product.models import ProductVariant


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    color = models.CharField(max_length=50, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.total_amount = self.product_variant.price * self.quantity
        if self.quantity > 5:
            self.quantity = 5
        if self.quantity > self.product_variant.quantity:
            raise ValueError("Quantity exceeds available stock.")
        super().save(*args, **kwargs)

    def get_variant_image(self):
        primary_image = self.product_variant.images.filter(is_primary=True).first()
        return primary_image.image.url if primary_image else None

    def __str__(self):
        return f"{self.product_variant.product.name} - {self.product_variant} x {self.quantity}"
