from django.urls import path
from .views import (
    HabitacionCreateView, HabitacionListView, ReservaListEmpleadoView,
    ReservaUpdateEstadoView, ReservaEmpleadoCreateView,
    HotelHabitacionesListView, ReservaUsuarioCreateView,
    MisReservasListView, ReservasInicioView, ReporteContableView
)

urlpatterns = [
    path('inicio/', ReservasInicioView.as_view(), name='reserves-inicio'),

    path('habitaciones/crear/', HabitacionCreateView.as_view(), name='crear-habitacion'),
    path('habitaciones/', HabitacionListView.as_view(), name='lista-habitaciones'),

    path('reservas/', ReservaListEmpleadoView.as_view(), name='lista-reservas-empleado'),
    path('reservas/estado/<int:pk>/', ReservaUpdateEstadoView.as_view(), name='actualizar-estado-reserva'),
    path('reservas/crear/', ReservaEmpleadoCreateView.as_view(), name='crear-reserva-empleado'),

    path('hotel/<int:hotel_id>/habitaciones/', HotelHabitacionesListView.as_view(), name='hotel-habitaciones'),
    path('reservar/', ReservaUsuarioCreateView.as_view(), name='crear-reserva-usuario'),
    path('mis-reservas/', MisReservasListView.as_view(), name='mis-reservas'),
    path('reporte-contable/', ReporteContableView.as_view(), name='ver-reporte-contable'),
]
