from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Meta:
        app_label = 'profiles'  # Esto ayuda a resolver ambigüedades

    def __str__(self):
        return self.username