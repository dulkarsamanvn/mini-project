from datetime import date
from category.models import Category
from brand.models import Brand
from django.db import models
from django.utils import timezone
from decimal import Decimal

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

# ------------------------------------------------------------
    def get_discounted_price(self):
        from offer_management.models import Offer
        """
        Calculate the discounted price for the product variant
        based on the highest applicable category or product offer.
        """
        today = date.today()

        # Get category offers
        category_offers = Offer.objects.filter(
            offer_type='category',
            category=self.product.category,
            end_date__gte=today
        ).order_by('-discount')

        # Get product offers
        product_offers = Offer.objects.filter(
            offer_type='product',
            product=self.product,
            end_date__gte=today
        ).order_by('-discount')

        # Determine the highest discount
        category_discount = category_offers.first().discount if category_offers.exists() else 0
        product_discount = product_offers.first().discount if product_offers.exists() else 0

        highest_discount = max(category_discount, product_discount)

        # Calculate discounted price
        discounted_price = self.price * (1 - (highest_discount / Decimal('100')))
        return round(discounted_price, 2)
    
    # ---------------------------------------------------------------------

    @property
    def dynamic_status(self):
        """Determine stock status based on quantity"""
        return 'Out of Stock' if self.quantity == 0 else 'In Stock'



    def __str__(self):
        return f"{self.product.name} - {self.case_color} case, {self.dial_color} dial, {self.strap_material} strap"

class ProductVariantImage(models.Model):
    """Images for Product Variants"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_variants/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.variant}"
