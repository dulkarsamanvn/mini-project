from django.db import models
from django.conf import settings
from django.utils.timezone import now
from profile_management.models import Address
from product.models import ProductVariant
from offer_management.models import Coupon
# Create your models here.




class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELED', 'Canceled'),
        ('RETURN_PENDING', 'Return pending'),
        ('RETURNED','Returned'),
        ('PAYMENT_PENDING', 'Payment Pending'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('RAZORPAY', 'Razorpay'),
        ('CASH_ON_DELIVERY', 'Cash on Delivery'),
        ('UPI', 'UPI'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=now)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)


    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_status = models.CharField(max_length=50, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.razorpay_payment_status != 'PAID' and self.payment_method=='razorpay':
            self.order_status = 'PAYMENT_PENDING'
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)


# --------------------------------------------------------------------------------

class ReturnReason(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='return_reasons')
    sizing_issues = models.BooleanField(default=False)
    damaged_item = models.BooleanField(default=False)
    incorrect_order = models.BooleanField(default=False)
    delivery_delays = models.BooleanField(default=False)
    other_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved=models.BooleanField(default=False)

    def __str__(self):
        return f"Return Reason for Order #{self.order.id} - Created on {self.created_at}"





    