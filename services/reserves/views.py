import re
from django.db.models import Case, When, Value, IntegerField, Sum, Count
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import TruncMonth
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.decorators.clickjacking import xframe_options_exempt

from .models import Habitacion, Reserva, ReservaHabitacion, ComprobantePago
from services.profiles.models import User, Empleado
import io
import base64
import matplotlib.pyplot as plt
from django.utils.timezone import now
from django.views.generic import TemplateView, UpdateView, CreateView


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
        numero = request.POST.get('numero')
        descripcion = request.POST.get('descripcion')
        precio_noche = request.POST.get('precio_noche')
        tipo = request.POST.get('tipo')
        estado = request.POST.get('estado', 'disponible')

        hotel = request.user.empleado.hotel
        Habitacion.objects.create(
            numero=numero,
            descripcion=descripcion,
            precio_noche=precio_noche,
            tipo=tipo,
            estado=estado,
            hotel=hotel
        )
        return redirect('lista-habitaciones')


# 📋 Lista habitaciones
class HabitacionListView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        habitaciones = Habitacion.objects.filter(hotel=request.user.empleado.hotel)
        return render(request, 'reserves/habitacion_list.html', {'habitaciones': habitaciones})


# 📅 Ver reservas del hotel
class ReservaListEmpleadoView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        # Anotar las reservas para ordenar: 0 si es pendiente, 1 si es finalizado
        reservas = Reserva.objects.filter(hotel=request.user.empleado.hotel).annotate(
            orden_estado=Case(
                When(estado="finalizado", then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('orden_estado', '-fecha_checkin')  # Pendientes primero, más recientes primero

        reservas_con_habitaciones = []

        for reserva in reservas:
            habitaciones = ReservaHabitacion.objects.filter(reserva=reserva).select_related('habitacion')
            reservas_con_habitaciones.append({
                'reserva': reserva,
                'habitaciones': habitaciones
            })

        return render(request, 'reserves/reserva_list_empleado.html', {
            'reservas_con_habitaciones': reservas_con_habitaciones
        })

# 🔁 Cambiar estado de una reserva
@method_decorator(xframe_options_exempt, name='dispatch')
class ReservaUpdateEstadoView(UpdateView):
    model = Reserva
    fields = ['estado']  # Solo el campo que quieres editar
    template_name = 'reserves/reserva_estado_form.html'
    success_url = reverse_lazy('lista-reservas-empleado')

# 📝 Crear reserva como empleado
class ReservaEmpleadoCreateView(View):
    def get(self, request):
        habitaciones = Habitacion.objects.filter(hotel=request.user.empleado.hotel, estado='disponible')
        return render(request, 'reserves/reserva_empleado_form.html', {'habitaciones': habitaciones})

    def post(self, request):
        tipo_usuario = request.POST.get("tipo_usuario")
        cedula = request.POST.get("cedula_usuario")
        cedula_normalizada = re.sub(r"[-\s]", "", cedula)

        usuario = User.objects.filter(numero_cedula=cedula_normalizada, rol="usuario").first()

        if tipo_usuario == "registrado":
            if not usuario:
                messages.error(request, "Usuario no encontrado con esa cédula.")
                return render(request, 'reserves/reserva_empleado_form.html', {
                    'habitaciones': Habitacion.objects.filter(hotel=request.user.empleado.hotel)
                })
        else:
            usuario = User.objects.create_user(
                username=f"user_{cedula_normalizada}",
                first_name=request.POST.get("nombre"),
                last_name=request.POST.get("apellido"),
                email=request.POST.get("correo_usuario"),
                telefono=request.POST.get("telefono"),
                numero_cedula=cedula_normalizada,
                rol="usuario",
                password="12345678"
            )

        fecha_checkin = request.POST.get("fecha_checkin")
        fecha_checkout = request.POST.get("fecha_checkout")
        habitaciones_ids = request.POST.getlist("habitaciones")

        habitaciones_ocupadas = []
        habitaciones_disponibles = []

        for habitacion_id in habitaciones_ids:
            habitacion = Habitacion.objects.get(id=habitacion_id)

            reservas_conflicto = ReservaHabitacion.objects.filter(
                habitacion=habitacion,
                reserva__fecha_checkin__lt=fecha_checkout,
                reserva__fecha_checkout__gt=fecha_checkin
            )

            if reservas_conflicto.exists():
                habitaciones_ocupadas.append(habitacion.numero)
            else:
                habitaciones_disponibles.append(habitacion)

        if habitaciones_ocupadas:
            mensaje_error = f"La(s) habitación(es) {', '.join(habitaciones_ocupadas)} ya están ocupadas en esas fechas."
            messages.error(request, mensaje_error)
            return render(request, 'reserves/reserva_empleado_form.html', {
                'habitaciones': Habitacion.objects.filter(hotel=request.user.empleado.hotel)
            })


        reserva = Reserva.objects.create(
            fecha_checkin=fecha_checkin,
            fecha_checkout=fecha_checkout,
            metodo_pago=request.POST.get("metodo_pago"),
            usuario=usuario,
            empleado=request.user.empleado,
            hotel=request.user.empleado.hotel,
            monto_total=0
        )

        total = 0
        for habitacion in habitaciones_disponibles:
            ReservaHabitacion.objects.create(reserva=reserva, habitacion=habitacion)
            total += habitacion.precio_noche

        reserva.monto_total = total
        reserva.save()

        messages.success(request, "Reserva creada correctamente.")
        return redirect("lista-reservas-empleado")
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
        return render(request, 'reserves/reserva_estado_form.html')

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


class EmpleadoRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, 'empleado')

class ReporteContableView(LoginRequiredMixin, EmpleadoRequiredMixin, TemplateView):
    template_name = 'reserves/reporte_contable.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener el hotel del empleado que accede
        hotel = self.request.user.empleado.hotel

        # Filtrar solo las reservas finalizadas de ese hotel
        reservas_finalizadas = Reserva.objects.filter(estado='finalizada', hotel=hotel)

        # Calcular ingresos totales y promedio de ventas (asumiendo último mes o 30 días)
        total_ingresos = float(reservas_finalizadas.aggregate(Sum('monto_total'))['monto_total__sum'] or 0)
        promedio_ventas = round(total_ingresos / 30, 2)

        context['total_ingresos'] = total_ingresos
        context['promedio_ventas'] = promedio_ventas

        # === Gráfico de pastel: distribución por estado (solo del hotel del empleado) ===
        distribucion = Reserva.objects.filter(hotel=hotel).values('estado').annotate(total=Count('id'))
        labels = [d['estado'].capitalize() for d in distribucion]
        sizes = [d['total'] for d in distribucion]

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        plt.title('Distribución de Reservas por Estado')

        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png')
        plt.close(fig1)
        buf1.seek(0)
        image_base64_1 = base64.b64encode(buf1.getvalue()).decode('utf-8')

        context['grafico_estado_base64'] = image_base64_1

        # === Gráfico de barras: ingresos por mes (solo del hotel del empleado) ===
        ventas_mensuales = (
            reservas_finalizadas
            .annotate(mes=TruncMonth('fecha_reserva'))
            .values('mes')
            .annotate(total=Sum('monto_total'))
            .order_by('mes')
        )

        meses = [v['mes'].strftime('%b %Y') for v in ventas_mensuales]
        ingresos = [float(v['total']) for v in ventas_mensuales]

        if ingresos:
            max_ingreso = float(max(ingresos))
            min_ingreso = float(min(ingresos))
            rango = max_ingreso - min_ingreso
            umbral_alto = min_ingreso + 0.66 * rango
            umbral_medio = min_ingreso + 0.33 * rango

            colores = []
            for ingreso in ingresos:
                if ingreso >= umbral_alto:
                    colores.append('blue')  # Alto
                elif ingreso >= umbral_medio:
                    colores.append('orange')  # Medio
                else:
                    colores.append('red')  # Bajo
        else:
            colores = ['gray'] * len(meses)

        fig2, ax2 = plt.subplots()
        ax2.bar(meses, ingresos, color=colores, width=0.1)
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Ingresos ($)')
        plt.title('Ingresos por Mes')
        plt.tight_layout()

        buf2 = io.BytesIO()
        plt.savefig(buf2, format='png')
        plt.close(fig2)
        buf2.seek(0)
        image_base64_2 = base64.b64encode(buf2.getvalue()).decode('utf-8')

        context['grafico_barras_base64'] = image_base64_2

        return context


class ReservaCreateView(CreateView):
    model = Reserva
    template_name = 'reserves/reserva_usuario.html'
    fields = ['fecha_checkin', 'fecha_checkout', 'correo', 'telefono', 'metodo_pago']

    def form_valid(self, form):
        reserva = form.save(commit=False)
        reserva.usuario = self.request.user if self.request.user.is_authenticated else None
        reserva.hotel = ... # Puedes asignar el hotel aquí según el flujo
        reserva.monto_total = 0  # Lógica real de cálculo aquí
        reserva.save()

        # Manejo del comprobante si viene del POST
        comprobante = self.request.FILES.get('archivo_comprobante')
        if form.cleaned_data.get('metodo_pago') == 'deposito' and comprobante:
            ComprobantePago.objects.create(
                reserva=reserva,
                archivo_comprobante=comprobante
            )

        messages.success(self.request, "Reserva creada exitosamente.")
        return redirect('inicio')  # Reemplaza con tu URL real