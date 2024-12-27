from django.db import models
from django.conf import settings


# Create your models here.
class Wallet(models.Model):
    user=models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email}'s Wallet" 

    def credit(self, amount, description=""):
        """
        Add amount to the wallet balance and log a credit transaction.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive for credit.")
        self.balance += amount
        self.save()
        self.transactions.create(
            transaction_type='credit',
            amount=amount,
            description=description
        )

    def debit(self, amount, description=""):
        """
        Deduct amount from the wallet balance and log a debit transaction.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive for debit.")
        if self.balance < amount:
            raise ValueError("Insufficient balance for this transaction.")
        self.balance -= amount
        self.save()
        self.transactions.create(
            transaction_type='debit',
            amount=amount,
            description=description
        )


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - ₹{self.amount}"
