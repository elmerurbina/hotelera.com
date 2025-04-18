from pathlib import Path
import sys
from django.apps import apps




# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


STATICFILES_DIRS = [
    BASE_DIR / "static",  # Aquí se indica la ubicación de tu carpeta de archivos estáticos
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGOUT_REDIRECT_URL = 'pagina_logout'

SECRET_KEY = "django-insecure-l^b$zy4wjy(hx@f#60k%6!5a@zwuwmp8uw!7)xua0^zzzv_obb"
DEBUG = True
ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "services.profiles",
    "services.reserves",
    "services.online_payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "hotelera.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "hotelera.wsgi.application"


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hotelera',  # Nombre de la base de datos
        'USER': 'root',            # Tu nombre de usuario de MySQL
        'PASSWORD': '7>>HhNN6/fZ',     # Tu contraseña de MySQL
        'HOST': 'localhost',                   # Si estás usando MySQL en el mismo servidor, usa 'localhost'
        'PORT': '3306',                        # Puerto por defecto de MySQL
    }
}


AUTH_USER_MODEL = 'profiles.User'


# Verificación explícita del modelo de usuario
try:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    print(f"Modelo de usuario cargado correctamente: {User.__module__}.{User.__name__}", file=sys.stderr)
except Exception as e:
    print(f"ERROR al cargar AUTH_USER_MODEL: {str(e)}", file=sys.stderr)

# Debug: Validación de contraseñas
print("\n=== VALIDACIÓN DE CONTRASEÑAS ===", file=sys.stderr)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]



LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


try:
    from django.apps import apps

    for app_config in apps.get_app_configs():

        try:
            print(f"  Modelos: {list(app_config.models.keys())}", file=sys.stderr)
        except Exception as e:
            print(f"  Error al cargar modelos: {str(e)}", file=sys.stderr)

    # Verificación especial para la app profiles
    try:
        profiles_config = apps.get_app_config('profiles')
        print("\nConfiguración de profiles:", file=sys.stderr)
        print(f"Nombre: {profiles_config.name}", file=sys.stderr)
        print(f"Label: {profiles_config.label}", file=sys.stderr)
        print(f"Modelos: {list(profiles_config.models.keys())}", file=sys.stderr)

        # Verificar si el modelo User está registrado
        if 'user' in profiles_config.models:
            print("Modelo User encontrado en profiles", file=sys.stderr)
        else:
            print("ADVERTENCIA: Modelo User no encontrado en profiles", file=sys.stderr)
    except LookupError:
        print("ERROR: No se pudo encontrar la app 'profiles'", file=sys.stderr)

except Exception as e:
    print(f"ERROR en verificación de apps: {str(e)}", file=sys.stderr)


try:
    from django.conf import settings
    from importlib import import_module

    for middleware in settings.MIDDLEWARE:
        print(f"Middleware: {middleware}", file=sys.stderr)
        try:
            module_path, class_name = middleware.rsplit('.', 1)
            module = import_module(module_path)
            middleware_class = getattr(module, class_name)
            print(f"  Cargado correctamente: {middleware_class}", file=sys.stderr)
        except Exception as e:
            print(f"  ERROR al cargar: {str(e)}", file=sys.stderr)

except Exception as e:
    print(f"ERROR en verificación de middleware: {str(e)}", file=sys.stderr)

print("\n=== FIN DE CARGA settings.py ===\n", file=sys.stderr)


# Función para debug adicional cuando las apps están completamente cargadas
def debug_after_load():
    print("\n=== DEBUG POST-LOAD ===", file=sys.stderr)
    try:
        from django.apps import apps
        from django.contrib.auth import get_user_model

        print("Aplicaciones completamente cargadas:", file=sys.stderr)
        for app_config in apps.get_app_configs():
            print(f"- {app_config.name}", file=sys.stderr)

        User = get_user_model()
        print(f"\nModelo de usuario obtenido: {User.__module__}.{User.__name__}", file=sys.stderr)

    except Exception as e:
        print(f"ERROR en debug post-load: {str(e)}", file=sys.stderr)


# Registrar función para ejecutar después de cargar todo
import atexit

atexit.register(debug_after_load)