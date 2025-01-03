# Generated by Django 5.1.3 on 2024-12-28 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_alter_order_coupon_delete_coupon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELED', 'Canceled'), ('RETURNED', 'Returned')], default='PENDING', max_length=20),
        ),
    ]
