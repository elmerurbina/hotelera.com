import re
from datetime import datetime
import pytesseract
from PIL import Image
from django.views.decorators.csrf import csrf_exempt
from reportlab.pdfgen import canvas
from django.db.models import Case, When, Value, IntegerField, Sum, Count, ProtectedError
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.decorators.clickjacking import xframe_options_exempt
from reportlab.lib.pagesizes import letter
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
        return hasattr(self.request.user, "empleado")


# Vista principal tras login de empleados
class ReservasInicioView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        return render(request, "reserves/inicio_empleado.html")


# 🛏 Crear habitación
class HabitacionCreateView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        return render(request, "reserves/habitacion_form.html")

    def post(self, request):
        numero = request.POST.get("numero")
        descripcion = request.POST.get("descripcion")
        precio_noche = request.POST.get("precio_noche")
        tipo = request.POST.get("tipo")
        estado = request.POST.get("estado", "disponible")

        hotel = request.user.empleado.hotel
        Habitacion.objects.create(
            numero=numero,
            descripcion=descripcion,
            precio_noche=precio_noche,
            tipo=tipo,
            estado=estado,
            hotel=hotel,
        )
        return redirect("lista-habitaciones")


# 📋 Ver Lista habitaciones
class HabitacionListView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        habitaciones = Habitacion.objects.filter(
            hotel=request.user.empleado.hotel
        )
        return render(
            request,
            "reserves/habitacion_list.html",
            {"habitaciones": habitaciones},
        )


# Editar Habitacion
class HabitacionEditView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def post(self, request):
        habitacion_id = request.POST.get("id")
        numero = request.POST.get("numero")
        tipo = request.POST.get("tipo")
        descripcion = request.POST.get("descripcion")
        precio_noche = request.POST.get("precio_noche")
        estado = request.POST.get("estado")

        try:
            habitacion = Habitacion.objects.get(
                id=habitacion_id, hotel=request.user.empleado.hotel
            )
            habitacion.numero = numero
            habitacion.tipo = tipo
            habitacion.descripcion = descripcion
            habitacion.precio_noche = precio_noche
            habitacion.estado = estado
            habitacion.save()

            messages.success(
                request,
                f"La habitación {habitacion.numero} fue actualizada correctamente.",
            )
        except Habitacion.DoesNotExist:
            messages.error(
                request,
                "Error: No se encontró la habitación que intentas editar.",
            )

        return redirect("lista-habitaciones")


# 🗑 Eliminar habitación
class HabitacionDeleteView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def post(self, request):
        habitacion_id = request.POST.get("id")

        try:
            habitacion = Habitacion.objects.get(
                id=habitacion_id,
                hotel=request.user.empleado.hotel
            )
            numero_habitacion = habitacion.numero
            habitacion.delete()

            messages.success(
                request,
                f"La habitación {numero_habitacion} fue eliminada correctamente."
            )
        except Habitacion.DoesNotExist:
            messages.error(
                request,
                "Error: No se encontró la habitación que intentas eliminar."
            )

        return redirect("lista-habitaciones")

# 📅 Ver reservas del hotel
class ReservaListEmpleadoView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request):
        # Anotar las reservas para ordenar: 0 si es pendiente, 1 si es finalizado, 2 si es cancelado
        reservas = (
            Reserva.objects.filter(hotel=request.user.empleado.hotel)
            .annotate(
                orden_estado=Case(
                    When(
                        estado="finalizada", then=Value(2)
                    ),  # Estado finalizado al final
                    When(
                        estado="cancelada", then=Value(3)
                    ),  # Estado cancelado al final
                    default=Value(
                        1
                    ),  # Estado pendiente (default) al principio
                    output_field=IntegerField(),
                )
            )
            .order_by("orden_estado", "-fecha_checkin")
        )

        reservas_con_habitaciones = []

        for reserva in reservas:
            habitaciones = ReservaHabitacion.objects.filter(
                reserva=reserva
            ).select_related("habitacion")
            reservas_con_habitaciones.append(
                {"reserva": reserva, "habitaciones": habitaciones}
            )

        return render(
            request,
            "reserves/reserva_list_empleado.html",
            {"reservas_con_habitaciones": reservas_con_habitaciones},
        )


# 🔁 Cambiar estado de una reserva
@method_decorator(xframe_options_exempt, name="dispatch")
@method_decorator(
    csrf_exempt, name="dispatch"
)  # Asegurarnos que no bloqueen el CSRF en un formulario AJAX
class ReservaUpdateEstadoView(UpdateView):
    model = Reserva
    fields = ["estado"]  # Solo el campo que quieres editar
    template_name = "reserves/reserva_estado_form.html"
    success_url = reverse_lazy(
        "lista-reservas-empleado"
    )  # URL de éxito si es necesario redirigir

    def form_valid(self, form):
        # Procesamos el formulario y cambiamos el estado de la reserva
        reserva = form.save(commit=False)
        reserva.save()

        # Devuelve una respuesta JSON para manejarla en el modal
        return JsonResponse(
            {"success": True, "message": "Estado actualizado con éxito."}
        )

    def form_invalid(self, form):
        # Si hay un error con el formulario
        return JsonResponse(
            {
                "success": False,
                "message": "Hubo un error al actualizar el estado.",
            }
        )


# 📝 Crear reserva como empleado
class ReservaEmpleadoCreateView(View):
    def get(self, request):
        habitaciones = Habitacion.objects.filter(
            hotel=request.user.empleado.hotel, estado="disponible"
        )
        return render(
            request,
            "reserves/reserva_empleado_form.html",
            {"habitaciones": habitaciones},
        )

    def post(self, request):
        tipo_usuario = request.POST.get("tipo_usuario")
        cedula = request.POST.get("cedula_usuario")
        cedula_normalizada = re.sub(r"[-\s]", "", cedula)

        usuario = User.objects.filter(
            numero_cedula=cedula_normalizada, rol="usuario"
        ).first()

        if tipo_usuario == "registrado":
            if not usuario:
                messages.error(
                    request, "Usuario no encontrado con esa cédula."
                )
                return render(
                    request,
                    "reserves/reserva_empleado_form.html",
                    {
                        "habitaciones": Habitacion.objects.filter(
                            hotel=request.user.empleado.hotel
                        )
                    },
                )
        else:
            usuario = User.objects.create_user(
                username=f"user_{cedula_normalizada}",
                first_name=request.POST.get("nombre"),
                last_name=request.POST.get("apellido"),
                email=request.POST.get("correo_usuario"),
                telefono=request.POST.get("telefono"),
                numero_cedula=cedula_normalizada,
                rol="usuario",
                password="12345678",
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
                reserva__fecha_checkout__gt=fecha_checkin,
            )

            if reservas_conflicto.exists():
                habitaciones_ocupadas.append(habitacion.numero)
            else:
                habitaciones_disponibles.append(habitacion)

        if habitaciones_ocupadas:
            mensaje_error = f"La(s) habitación(es) {', '.join(habitaciones_ocupadas)} ya están ocupadas en esas fechas."
            messages.error(request, mensaje_error)
            return render(
                request,
                "reserves/reserva_empleado_form.html",
                {
                    "habitaciones": Habitacion.objects.filter(
                        hotel=request.user.empleado.hotel
                    )
                },
            )

        reserva = Reserva.objects.create(
            fecha_checkin=fecha_checkin,
            fecha_checkout=fecha_checkout,
            metodo_pago=request.POST.get("metodo_pago"),
            usuario=usuario,
            empleado=request.user.empleado,
            hotel=request.user.empleado.hotel,
            monto_total=0,
        )

        total = 0
        for habitacion in habitaciones_disponibles:
            ReservaHabitacion.objects.create(
                reserva=reserva, habitacion=habitacion
            )
            total += habitacion.precio_noche

        reserva.monto_total = total
        reserva.save()

        messages.success(request, "Reserva creada correctamente.")
        return redirect("lista-reservas-empleado")


class ReservaEditView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def get(self, request, pk):
        reserva = get_object_or_404(
            Reserva,
            id=pk,
            hotel=request.user.empleado.hotel
        )

        # Obtener habitaciones actuales de la reserva
        habitaciones_reserva = [rh.habitacion.id for rh in ReservaHabitacion.objects.filter(reserva=reserva)]

        # Obtener todas las habitaciones disponibles del hotel
        habitaciones_disponibles = Habitacion.objects.filter(
            hotel=request.user.empleado.hotel
        )

        return render(request, "reserves/reserva_edit.html", {
            "reserva": reserva,
            "habitaciones_reserva": habitaciones_reserva,
            "habitaciones": habitaciones_disponibles,
            "estados_reserva": ["finalizada", "pendiente", "cancelada", "completada"]
        })

    def post(self, request, pk):
        reserva = get_object_or_404(
            Reserva,
            id=pk,
            hotel=request.user.empleado.hotel
        )

        try:
            # Actualizar datos básicos de la reserva
            reserva.fecha_checkin = request.POST.get("fecha_checkin")
            reserva.fecha_checkout = request.POST.get("fecha_checkout")
            reserva.metodo_pago = request.POST.get("metodo_pago")
            reserva.estado = request.POST.get("estado")

            # Procesar habitaciones
            habitaciones_ids = request.POST.getlist("habitaciones")

            # Eliminar relaciones con habitaciones que ya no están seleccionadas
            ReservaHabitacion.objects.filter(reserva=reserva).exclude(
                habitacion_id__in=habitaciones_ids
            ).delete()

            # Agregar nuevas relaciones con habitaciones
            for habitacion_id in habitaciones_ids:
                ReservaHabitacion.objects.get_or_create(
                    reserva=reserva,
                    habitacion_id=habitacion_id
                )

            # Recalcular monto total
            total = sum(h.habitacion.precio_noche for h in reserva.reservahabitacion_set.all())
            reserva.monto_total = total

            reserva.save()

            messages.success(request, "Reserva actualizada correctamente")
            return redirect("lista-reservas-empleado")

        except Exception as e:
            messages.error(request, f"Error al actualizar la reserva: {str(e)}")
            return redirect("editar-reserva", pk=pk)


class ReservaDeleteView(LoginRequiredMixin, EmpleadoRequiredMixin, View):
    def post(self, request, pk):
        reserva = get_object_or_404(
            Reserva,
            id=pk,
            hotel=request.user.empleado.hotel
        )

        try:
            numero_reserva = reserva.id
            reserva.delete()
            messages.success(request, f"Reserva #{numero_reserva} eliminada correctamente")
        except ProtectedError:
            messages.error(request, "No se puede eliminar la reserva porque tiene registros asociados")
        except Exception as e:
            messages.error(request, f"Error al eliminar la reserva: {str(e)}")

        return redirect("lista-reservas-empleado")


# 🌐 Ver habitaciones disponibles para un hotel (usuarios)
class HotelHabitacionesListView(View):
    def get(self, request, hotel_id):
        habitaciones = Habitacion.objects.filter(
            hotel__id=hotel_id, estado="disponible"
        )
        return render(
            request,
            "reserves/hotel_habitaciones_list.html",
            {"habitaciones": habitaciones},
        )


# 📆 Crear reserva como usuario
class ReservaUsuarioCreateView(View):
    # Maneja la solicitud GET para mostrar el formulario
    def get(self, request, hotel_id):
        hotel = get_object_or_404(User, id=hotel_id, rol="hotel")
        habitaciones = Habitacion.objects.filter(
            hotel=hotel, estado="disponible"
        )  # Filtra solo las habitaciones disponibles

        # Agregar la variable `user_authenticated` al contexto
        user_authenticated = request.user.is_authenticated

        return render(
            request,
            "reserves/reserva_usuario.html",
            {
                "hotel": hotel,
                "habitaciones": habitaciones,
                "user_authenticated": user_authenticated,  # Pasar esta variable
            },
        )

    # Maneja la solicitud POST para crear la reserva
    def post(self, request, hotel_id):
        hotel = get_object_or_404(User, id=hotel_id, rol="hotel")

        # Obtener los datos del formulario
        fecha_checkin = request.POST.get("fecha_checkin")
        fecha_checkout = request.POST.get("fecha_checkout")
        metodo_pago = request.POST.get("metodo_pago")
        cedula = request.POST.get("cedula_usuario")
        telefono = request.POST.get("telefono")
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        archivo_comprobante = request.FILES.get("archivo_comprobante")

        # Validar fechas
        try:
            fecha_checkin = datetime.strptime(fecha_checkin, "%Y-%m-%d").date()
            fecha_checkout = datetime.strptime(
                fecha_checkout, "%Y-%m-%d"
            ).date()
        except ValueError:
            messages.error(request, "Formato de fecha inválido.")
            return redirect(request.path)

        # Comprobar si el usuario está autenticado
        if request.user.is_authenticated:
            usuario = (
                request.user
            )  # Si está autenticado, usar el usuario logeado
        else:
            # Si no está autenticado, buscar o crear un nuevo usuario con la cédula
            cedula_normalizada = re.sub(r"[-\s]", "", cedula)
            usuario = User.objects.filter(
                numero_cedula=cedula_normalizada, rol="usuario"
            ).first()

            if not usuario:
                usuario = User.objects.create_user(
                    username=f"user_{cedula_normalizada}",
                    first_name=nombre,
                    last_name=apellido,
                    telefono=telefono,
                    numero_cedula=cedula_normalizada,
                    rol="usuario",
                    password="12345678",  # Considera generar una contraseña aleatoria o segura
                )

        # Obtener las habitaciones seleccionadas
        habitaciones_ids = request.POST.getlist("habitaciones")
        habitaciones_disponibles = []
        habitaciones_ocupadas = []

        for habitacion_id in habitaciones_ids:
            habitacion = get_object_or_404(Habitacion, id=habitacion_id)
            reservas_conflicto = ReservaHabitacion.objects.filter(
                habitacion=habitacion,
                reserva__fecha_checkin__lt=fecha_checkout,
                reserva__fecha_checkout__gt=fecha_checkin,
            )
            if reservas_conflicto.exists():
                habitaciones_ocupadas.append(habitacion.numero)
            else:
                habitaciones_disponibles.append(habitacion)

        # Si hay habitaciones ocupadas, mostrar mensaje y detener
        if habitaciones_ocupadas:
            mensaje = f"La(s) habitación(es) {', '.join(habitaciones_ocupadas)} ya están ocupadas en esas fechas."
            messages.error(request, mensaje)
            return render(
                request,
                "reserves/reserva_usuario.html",
                {
                    "hotel": hotel,
                    "habitaciones": Habitacion.objects.filter(
                        hotel=hotel, estado="disponible"
                    ),
                },
            )

        # Si no hay habitaciones disponibles, mostrar mensaje y detener
        if not habitaciones_disponibles:
            messages.error(
                request,
                "No hay habitaciones disponibles para las fechas seleccionadas.",
            )
            return render(
                request,
                "reserves/reserva_usuario.html",
                {
                    "hotel": hotel,
                    "habitaciones": Habitacion.objects.filter(
                        hotel=hotel, estado="disponible"
                    ),
                },
            )

        # Crear la reserva, sin validar el comprobante de pago
        reserva = Reserva.objects.create(
            fecha_checkin=fecha_checkin,
            fecha_checkout=fecha_checkout,
            metodo_pago=metodo_pago,
            usuario=usuario,
            hotel=hotel,
            monto_total=0,
        )

        total = 0
        for habitacion in habitaciones_disponibles:
            ReservaHabitacion.objects.create(
                reserva=reserva, habitacion=habitacion
            )
            total += habitacion.precio_noche

        reserva.monto_total = total
        reserva.save()

        # Si se sube un comprobante, guardar el archivo en la base de datos
        if archivo_comprobante:
            ComprobantePago.objects.create(
                reserva=reserva, archivo_comprobante=archivo_comprobante
            )

        # ✅ Solo si pasa toda la validación, generamos el PDF:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        p.drawString(
            100, 750, f"Número de cédula del usuario: {usuario.numero_cedula}"
        )
        p.drawString(100, 730, f"Nombre del hotel: {hotel.nombre_hotel}")
        p.drawString(
            100,
            710,
            f"Número de habitación: {', '.join([hab.numero for hab in habitaciones_disponibles])}",
        )
        p.drawString(
            100,
            690,
            f"Check-in: {fecha_checkin} - Check-out: {fecha_checkout}",
        )
        p.drawString(100, 670, f"Total: ${total}")

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="reserva.pdf"'
        return response


# Ver reservas como usuario autenticado
class MisReservasView(View):
    # Muestra las reservas del usuario
    def get(self, request):
        if request.user.is_authenticated:
            reservas = Reserva.objects.filter(
                usuario=request.user
            )  # Filtra las reservas del usuario autenticado
            return render(
                request, "reserves/mis_reservas.html", {"reservas": reservas}
            )
        else:
            messages.error(
                request, "Por favor, inicie sesión para ver sus reservas."
            )
            return redirect("login")


class CancelarReservaView(View):
    # Permite al usuario cancelar una reserva
    def post(self, request, reserva_id):
        reserva = get_object_or_404(
            Reserva, id=reserva_id, usuario=request.user
        )

        # Verificar si la reserva se puede cancelar (solo puede cancelarse si está pendiente)
        if reserva.estado == "pendiente":
            reserva.estado = "cancelada"
            reserva.save()
            messages.success(
                request,
                f"La reserva {reserva.id} ha sido cancelada exitosamente.",
            )
        else:
            messages.error(
                request,
                f"La reserva {reserva.id} no puede ser cancelada porque ya está {reserva.estado}.",
            )

        return redirect("mis_reservas")  # Redirige al listado de reservas


class EmpleadoRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return hasattr(self.request.user, "empleado")


# Acceder al reporte contable
class ReporteContableView(
    LoginRequiredMixin, EmpleadoRequiredMixin, TemplateView
):
    template_name = "reserves/reporte_contable.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener el hotel del empleado que accede
        hotel = self.request.user.empleado.hotel

        # Filtrar solo las reservas finalizadas de ese hotel
        reservas_finalizadas = Reserva.objects.filter(
            estado="finalizada", hotel=hotel
        )

        # Calcular ingresos totales y promedio de ventas (asumiendo último mes o 30 días)
        total_ingresos = float(
            reservas_finalizadas.aggregate(Sum("monto_total"))[
                "monto_total__sum"
            ]
            or 0
        )
        promedio_ventas = round(total_ingresos / 30, 2)

        context["total_ingresos"] = total_ingresos
        context["promedio_ventas"] = promedio_ventas

        # === Gráfico de pastel: distribución por estado (solo del hotel del empleado) ===
        distribucion = (
            Reserva.objects.filter(hotel=hotel)
            .values("estado")
            .annotate(total=Count("id"))
        )
        labels = [d["estado"].capitalize() for d in distribucion]
        sizes = [d["total"] for d in distribucion]

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax1.axis("equal")
        plt.title("Distribución de Reservas por Estado")

        buf1 = io.BytesIO()
        plt.savefig(buf1, format="png")
        plt.close(fig1)
        buf1.seek(0)
        image_base64_1 = base64.b64encode(buf1.getvalue()).decode("utf-8")

        context["grafico_estado_base64"] = image_base64_1

        # === Gráfico de barras: ingresos por mes (solo del hotel del empleado) ===
        ventas_mensuales = (
            reservas_finalizadas.annotate(mes=TruncMonth("fecha_reserva"))
            .values("mes")
            .annotate(total=Sum("monto_total"))
            .order_by("mes")
        )

        meses = [v["mes"].strftime("%b %Y") for v in ventas_mensuales]
        ingresos = [float(v["total"]) for v in ventas_mensuales]

        if ingresos:
            max_ingreso = float(max(ingresos))
            min_ingreso = float(min(ingresos))
            rango = max_ingreso - min_ingreso
            umbral_alto = min_ingreso + 0.66 * rango
            umbral_medio = min_ingreso + 0.33 * rango

            colores = []
            for ingreso in ingresos:
                if ingreso >= umbral_alto:
                    colores.append("blue")  # Alto
                elif ingreso >= umbral_medio:
                    colores.append("orange")  # Medio
                else:
                    colores.append("red")  # Bajo
        else:
            colores = ["gray"] * len(meses)

        fig2, ax2 = plt.subplots()
        ax2.bar(meses, ingresos, color=colores, width=0.1)
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Ingresos ($)")
        plt.title("Ingresos por Mes")
        plt.tight_layout()

        buf2 = io.BytesIO()
        plt.savefig(buf2, format="png")
        plt.close(fig2)
        buf2.seek(0)
        image_base64_2 = base64.b64encode(buf2.getvalue()).decode("utf-8")

        context["grafico_barras_base64"] = image_base64_2

        return context
