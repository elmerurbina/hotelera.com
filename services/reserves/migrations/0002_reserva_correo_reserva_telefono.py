# Generated by Django 5.2 on 2025-04-11 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reserves", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reserva",
            name="correo",
            field=models.EmailField(
                default="hotelera.com@gmail.com", max_length=254, unique=True
            ),
        ),
        migrations.AddField(
            model_name="reserva",
            name="telefono",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
