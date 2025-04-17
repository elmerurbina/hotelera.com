from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROL_CHOICES = (
        ('usuario', 'Usuario Particular'),
        ('hotel', 'Hotel'),
        ('empleado', 'Empleado'),
    )

    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='usuario')

    # Campos comunes
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    # Campos exclusivos de usuario
    nombre_completo = models.CharField(max_length=255, blank=True, null=True)
    numero_cedula = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Número de cédula"
    )

    # Campos exclusivos de hotel
    nombre_hotel = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        nombre = f"{self.first_name} {self.last_name}".strip()
        return f"{nombre} ({self.numero_cedula or 'sin cédula'})"


class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Usuario registrado como empleado
    hotel = models.ForeignKey(User, on_delete=models.CASCADE, related_name="empleados")  # Hotel dueño
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} (Empleado de {self.hotel.nombre_hotel})"
