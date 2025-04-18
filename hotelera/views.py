from django.contrib.auth.views import LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from services.profiles.models import User


# Pagina de inicio
class HomeView(View):
    def get(self, request):
        hoteles = User.objects.filter(rol="hotel")
        # Mostrar los usuarios de tipo 'hotel' en la pagina principal
        return render(request, "index.html", {"hoteles": hoteles})


# Pagina perzonalida para el cierre de sesion
class CustomLogoutView(LogoutView):
    # Redirigir a una URL personalizada después de hacer logout
    next_page = reverse_lazy("pagina_logout")
