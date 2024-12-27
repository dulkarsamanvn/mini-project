from django.conf import settings
from django.db import models

class Address(models.Model):
    HOME = 'Home'
    WORK = 'Work'
    OTHER = 'Other'
    ADDRESS_TYPES = [
        (HOME, 'Home'),
        (WORK, 'Work'),
        (OTHER, 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Dynamically refers to the custom user model
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    name = models.CharField(max_length=255)  # Example: Home, Office
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default=HOME)
    phone = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.user.email}"  # Assuming CustomUser uses `email` as the unique identifier

    class Meta:
        ordering = ["-is_default", "name"]  # Default addresses first, then by name
