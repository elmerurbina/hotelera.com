# profiles/views.py
from django.contrib import messages
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Empleado


class LoginView(View):
    def get(self, request):
        return render(request, 'auth/login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Buscar al usuario por el correo electrónico
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'auth/login.html', {'error': 'Credenciales inválidas'})

        # Verificar si la contraseña es correcta
        if check_password(password, user.password):
            login(request, user)
            return redirect('home')  # Redirigir a la página de inicio o cualquier otra que desees
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

        # Capturar la imagen si se sube
        imagen_hotel = request.FILES.get('imagen_hotel')  # Capturamos la imagen

        # Crear el usuario
        user = User.objects.create(
            username=username,
            email=email,
            password=password,
            rol=rol,
            telefono=telefono,
            direccion=direccion,
            nombre_completo=nombre_completo if rol == 'usuario' else None,
            numero_cedula=numero_cedula if rol == 'usuario' else None,
            nombre_hotel=nombre_hotel if rol == 'hotel' else None,
            imagen_hotel=imagen_hotel if rol == 'hotel' else None  # Asignamos la imagen si es un hotel
        )

        # Iniciar sesión con el nuevo usuario
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
            rol='empleado'
        )

        Empleado.objects.create(user=empleado_user, hotel=request.user)
        return redirect('home')


class LoginEmpleadoView(View):
    def get(self, request):
        return render(request, 'auth/login_empleado.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user and Empleado.objects.filter(user=user).exists():
            login(request, user)
            return redirect('reserves-inicio')  # Nombre de la URL que redirige al panel de reservas
        else:
            return render(request, 'auth/login_empleado.html', {'error': 'Credenciales inválidas o no autorizado como empleado'})

class EliminarEmpleadoView(View):
    def post(self, request, *args, **kwargs):
        # Obtener el nombre de usuario desde el formulario
        username = request.POST.get('username')

        try:
            # Obtener el hotel (User con rol='hotel') de la sesión
            hotel_user = User.objects.get(id=request.user.id, rol='hotel')

            # Obtener el usuario a eliminar
            user_to_delete = User.objects.get(username=username)

            # Verificar si el usuario a eliminar es un empleado del hotel actual
            if Empleado.objects.filter(user=user_to_delete, hotel=hotel_user).exists():
                user_to_delete.delete()  # Eliminar el usuario
                messages.success(request, f'El usuario "{username}" fue eliminado exitosamente.')
            else:
                messages.error(request, 'Este usuario no está vinculado al hotel actual.')

        except User.DoesNotExist:
            messages.error(request, f'El usuario "{username}" no existe.')
        except Exception as e:
            messages.error(request, f'Hubo un error al intentar eliminar el usuario: {str(e)}')

        return redirect('registro_empleado')  # Redirigir al template de registro de empleados