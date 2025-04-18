from django.urls import path

from . import views
from .views import (
    HabitacionCreateView,
    HabitacionListView,
    ReservaListEmpleadoView,
    ReservaUpdateEstadoView,
    ReservaEmpleadoCreateView,
    HotelHabitacionesListView,
    ReservaUsuarioCreateView,
    ReservasInicioView,
    ReporteContableView,
    MisReservasView,
    CancelarReservaView,
)

urlpatterns = [
    path("inicio/", ReservasInicioView.as_view(), name="reserves-inicio"),
    path(
        "habitaciones/crear/",
        HabitacionCreateView.as_view(),
        name="crear-habitacion",
    ),
    path(
        "habitaciones/",
        HabitacionListView.as_view(),
        name="lista-habitaciones",
    ),
    path(
        "editar-habitacion/",
        views.HabitacionEditView.as_view(),
        name="editar-habitacion",
    ),
    path(
        "reservas/",
        ReservaListEmpleadoView.as_view(),
        name="lista-reservas-empleado",
    ),
    path(
        "reserva/<int:pk>/estado/",
        ReservaUpdateEstadoView.as_view(),
        name="cambiar-estado-reserva",
    ),
    path(
        "reservas/estado/<int:pk>/",
        ReservaUpdateEstadoView.as_view(),
        name="actualizar-estado-reserva",
    ),
    path(
        "reservas/crear/",
        ReservaEmpleadoCreateView.as_view(),
        name="crear-reserva-empleado",
    ),
    path(
        "hotel/<int:hotel_id>/habitaciones/",
        HotelHabitacionesListView.as_view(),
        name="hotel-habitaciones",
    ),
    path(
        "reservar/<int:hotel_id>/",
        ReservaUsuarioCreateView.as_view(),
        name="crear-reserva-usuario",
    ),
    path("mis_reservas/", MisReservasView.as_view(), name="mis_reservas"),
    path(
        "cancelar_reserva/<int:reserva_id>/",
        CancelarReservaView.as_view(),
        name="cancelar_reserva",
    ),
    path(
        "reporte-contable/",
        ReporteContableView.as_view(),
        name="ver-reporte-contable",
    ),
]
