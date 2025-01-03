# Generated by Django 5.1.3 on 2025-01-03 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_alter_order_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELED', 'Canceled'), ('RETURN_PENDING', 'Return pending'), ('RETURNED', 'Returned'), ('PAYMENT_PENDING', 'Payment Pending')], default='PENDING', max_length=20),
        ),
    ]
