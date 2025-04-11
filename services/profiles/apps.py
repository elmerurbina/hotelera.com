from django.apps import AppConfig

class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.profiles'
    label = 'profiles'  # Esto es crucial para resolver el conflicto
    verbose_name = 'User Profiles'