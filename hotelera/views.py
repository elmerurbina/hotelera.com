from django.contrib.auth.views import LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from services.profiles.models import User


class HomeView(View):
    def get(self, request):
        hoteles = User.objects.filter(rol='hotel')
        return render(request, 'index.html', {'hoteles': hoteles})

class CustomLogoutView(LogoutView):
    # Redirigir a una URL personalizada después de hacer logout
    next_page = reverse_lazy('pagina_logout')