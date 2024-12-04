from category.models import Category
from brand.models import Brand
from django.db import models
from django.utils import timezone

class Product(models.Model):
    """Main Product Model"""
    MOVEMENT_CHOICES = [
        ('automatic', 'Automatic'),
        ('quartz', 'Quartz'),
        ('manual', 'Manual'),
        ('solar', 'Solar'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey('category.Category', on_delete=models.SET_NULL, null=True, related_name='products')
    brand = models.ForeignKey('brand.Brand', on_delete=models.SET_NULL, null=True, related_name='products')
    created_at = models.DateTimeField(default=timezone.now)
    movement = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    """Product Variant Model"""
    STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    case_color = models.CharField(max_length=50)
    dial_color = models.CharField(max_length=50)
    strap_material = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')

    def __str__(self):
        return f"{self.product.name} - {self.case_color} case, {self.dial_color} dial, {self.strap_material} strap"

class ProductVariantImage(models.Model):
    """Images for Product Variants"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_variants/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.variant}"
