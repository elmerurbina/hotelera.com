# profiles/urls.py
from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import LoginView, RegistroUsuarioView, RegistroEmpleadoView, LoginEmpleadoView, EliminarEmpleadoView, \
    PerfilUsuarioView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('login-empleado/', LoginEmpleadoView.as_view(), name='login_empleado'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    path('registro-empleado/', RegistroEmpleadoView.as_view(), name='registro_empleado'),
    path('eliminar-empleado/', EliminarEmpleadoView.as_view(), name='eliminar_empleado'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('mi-perfil/', PerfilUsuarioView.as_view(), name='ver-perfil'),
]
