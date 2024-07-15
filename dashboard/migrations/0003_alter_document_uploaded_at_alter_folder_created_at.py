# Generated by Django 5.0.7 on 2024-07-12 05:14

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_document_uploaded_at_folder_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='uploaded_at',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='folder',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
