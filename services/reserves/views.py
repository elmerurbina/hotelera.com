from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Habitacion, Reserva, ReservaHabitacion
from services.profiles.models import User, Empleado


# Mixin para verificar si el usuario es empleado
class EmpleadoRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'empleado')


# Vista principal tras login de empleados
class ReservasInicioView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        return render(request, 'reserves/inicio_empleado.html')


# 🛏 Crear habitación
class HabitacionCreateView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        return render(request, 'reserves/habitacion_form.html')

    def post(self, request):
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        direccion = request.POST.get('direccion')
        estado = request.POST.get('estado', 'disponible')

        hotel = request.user.empleado.hotel
        Habitacion.objects.create(nombre=nombre, descripcion=descripcion, direccion=direccion, estado=estado, hotel=hotel)
        return redirect('lista-habitaciones')


# 📋 Lista habitaciones
class HabitacionListView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        habitaciones = Habitacion.objects.filter(hotel=request.user.empleado.hotel)
        return render(request, 'reserves/habitacion_list.html', {'habitaciones': habitaciones})


# 📅 Ver reservas del hotel
class ReservaListEmpleadoView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        reservas = Reserva.objects.filter(hotel=request.user.empleado.hotel)
        return render(request, 'reserves/reserva_list_empleado.html', {'reservas': reservas})


# 🔁 Cambiar estado de una reserva
class ReservaUpdateEstadoView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request, pk):
        reserva = get_object_or_404(Reserva, pk=pk)
        return render(request, 'reserves/reserva_estado_form.html', {'reserva': reserva})

    def post(self, request, pk):
        reserva = get_object_or_404(Reserva, pk=pk)
        nuevo_estado = request.POST.get('estado')
        reserva.estado = nuevo_estado
        reserva.save()
        return redirect('lista-reservas-empleado')


# 📝 Crear reserva como empleado
class ReservaEmpleadoCreateView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        return render(request, 'reserves/reserva_empleado_form.html')

    def post(self, request):
        correo_usuario = request.POST.get('correo_usuario')
        habitaciones_ids = request.POST.getlist('habitaciones')
        usuario = get_object_or_404(User, email=correo_usuario, rol='usuario')
        hotel = request.user.empleado.hotel
        empleado = request.user.empleado

        reserva = Reserva.objects.create(usuario=usuario, hotel=hotel, empleado=empleado)

        for habitacion_id in habitaciones_ids:
            habitacion = get_object_or_404(Habitacion, id=habitacion_id)
            ReservaHabitacion.objects.create(reserva=reserva, habitacion=habitacion)

        return redirect('lista-reservas-empleado')


# 🌐 Ver habitaciones disponibles para un hotel (usuarios)
class HotelHabitacionesListView(View):
    def get(self, request, hotel_id):
        habitaciones = Habitacion.objects.filter(hotel__id=hotel_id, estado='disponible')
        return render(request, 'reserves/hotel_habitaciones_list.html', {'habitaciones': habitaciones})


# 📆 Crear reserva como usuario
class ReservaUsuarioCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.rol == 'usuario'

    def get(self, request):
        return render(request, 'reserves/reserva_form.html')

    def post(self, request):
        hotel_id = request.POST.get('hotel_id')
        habitaciones_ids = request.POST.getlist('habitaciones')
        monto_total = request.POST.get('monto_total')

        reserva = Reserva.objects.create(
            usuario=request.user,
            hotel_id=hotel_id,
            monto_total=monto_total
        )

        for habitacion_id in habitaciones_ids:
            habitacion = get_object_or_404(Habitacion, id=habitacion_id)
            ReservaHabitacion.objects.create(reserva=reserva, habitacion=habitacion)

        return redirect('mis-reservas')


# 👀 Ver mis reservas
class MisReservasListView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.rol == 'usuario'

    def get(self, request):
        reservas = Reserva.objects.filter(usuario=request.user)
        return render(request, 'reserves/mis_reservas.html', {'reservas': reservas})
