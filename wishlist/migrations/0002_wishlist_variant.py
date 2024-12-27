# Generated by Django 5.1.3 on 2024-12-17 15:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
        ('wishlist', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wishlist',
            name='variant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='product.productvariant'),
        ),
    ]