from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from services.profiles.models import User


class HomeView(View):
    def get(self, request):
        hoteles = User.objects.filter(rol='hotel')
        return render(request, 'index.html', {'hoteles': hoteles})
