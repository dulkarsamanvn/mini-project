# Generated by Django 5.1.3 on 2024-12-30 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_returnreason'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnreason',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]