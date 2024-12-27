# Generated by Django 5.1.3 on 2024-12-19 13:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offer_management', '0001_initial'),
        ('orders', '0003_remove_order_razorpay_refund_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='coupon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='offer_management.coupon'),
        ),
        migrations.DeleteModel(
            name='Coupon',
        ),
    ]