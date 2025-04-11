# profiles/urls.py
from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import LoginView, RegistroUsuarioView, RegistroEmpleadoView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro_usuario'),
    path('registro-empleado/', RegistroEmpleadoView.as_view(), name='registro_empleado'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
