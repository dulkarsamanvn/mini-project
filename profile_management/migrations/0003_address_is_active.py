# Generated by Django 5.1.3 on 2024-12-12 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profile_management', '0002_address_address_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]