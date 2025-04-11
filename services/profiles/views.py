# profiles/views.py
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from .models import User, Empleado


class LoginView(View):
    def get(self, request):
        return render(request, 'auth/login.html')

    def post(self, request):
        email = request.POST.get('email')  # Cambié de 'username' a 'email'
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)  # Usar email en authenticate
        if user:
            login(request, user)
            return redirect('home')  # Redirige a la página principal después de un login exitoso
        else:
            return render(request, 'auth/login.html', {'error': 'Credenciales inválidas'})

class RegistroUsuarioView(View):
    def get(self, request):
        return render(request, 'auth/registro_usuario.html')

    def post(self, request):
        rol = request.POST.get('rol')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = make_password(request.POST.get('password'))

        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        nombre_completo = request.POST.get('nombre_completo')
        numero_cedula = request.POST.get('numero_cedula')
        nombre_hotel = request.POST.get('nombre_hotel')

        user = User.objects.create(
            username=username,
            email=email,
            password=password,
            rol=rol,
            telefono=telefono,
            direccion=direccion,
            nombre_completo=nombre_completo if rol == 'usuario' else None,
            numero_cedula=numero_cedula if rol == 'usuario' else None,
            nombre_hotel=nombre_hotel if rol == 'hotel' else None
        )

        login(request, user)
        return redirect('home')


class RegistroEmpleadoView(View):
    def get(self, request):
        if not request.user.is_authenticated or request.user.rol != 'hotel':
            return redirect('login')
        return render(request, 'auth/registro_empleado.html')

    def post(self, request):
        if not request.user.is_authenticated or request.user.rol != 'hotel':
            return redirect('login')

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = make_password(request.POST.get('password'))

        empleado_user = User.objects.create(
            username=username,
            email=email,
            password=password,
            rol='usuario'  # o 'empleado' si luego defines ese rol
        )

        Empleado.objects.create(user=empleado_user, hotel=request.user)
        return redirect('admin:index')
