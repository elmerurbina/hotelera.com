from django.db import models
from services.profiles.models import User, Empleado

class Habitacion(models.Model):
    ESTADO_CHOICES = (
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'Mantenimiento'),
    )

    hotel = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'rol': 'hotel'})
    numero = models.CharField(max_length=10)
    descripcion = models.TextField()
    precio_noche = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=50)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='disponible')

    def __str__(self):
        return f"Habitación {self.numero} - {self.hotel.nombre_hotel}"


class Reserva(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('finalizada', 'Finalizada'),
    )

    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_checkin = models.DateField()
    fecha_checkout = models.DateField()
    correo = models.EmailField(max_length=254, null=False, unique=True, default="hotelera.com@gmail.com")
    telefono = models.CharField(max_length=20, null=True, blank=True)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=50)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas_cliente', limit_choices_to={'rol': 'usuario'})
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas_gestionadas')
    hotel = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas', limit_choices_to={'rol': 'hotel'})

    def __str__(self):
        return f"Reserva #{self.id} - {self.hotel.nombre_hotel}"


class ReservaHabitacion(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)

    def __str__(self):
        return f"Reserva {self.reserva.id} - Habitación {self.habitacion.numero}"


class ComprobantePago(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='comprobantes')
    archivo_comprobante = models.FileField(upload_to='comprobantes/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comprobante de Reserva {self.reserva.id}"


class ReporteContable(models.Model):
    generado_por = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    archivo_excel = models.FileField(upload_to='reportes/')

    def __str__(self):
        return f"Reporte {self.id} generado por {self.generado_por.user.username}"
