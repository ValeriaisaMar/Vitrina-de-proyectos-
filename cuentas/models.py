"""Modelo de usuario de la Vitrina.

Se usa un usuario propio (no el que trae Django) para que:
- se inicie sesión con el correo, que es único y sin distinguir mayúsculas;
- cada persona tenga un rol: estudiante, profesor o admin;
- los campos queden en español, como pide la constitución.
"""

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cuentas.managers import UsuarioManager


class Rol(models.TextChoices):
    """Roles con cuenta. El visitante no tiene cuenta, por eso no aparece aquí."""

    ESTUDIANTE = "estudiante", _("Estudiante")
    PROFESOR = "profesor", _("Profesor")
    ADMIN = "admin", _("Admin")


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Persona con cuenta en la plataforma."""

    email = models.EmailField(_("correo electrónico"), unique=True)
    nombres = models.CharField(_("nombres"), max_length=80)
    apellidos = models.CharField(_("apellidos"), max_length=80)
    rol = models.CharField(_("rol"), max_length=12, choices=Rol.choices, default=Rol.ESTUDIANTE)

    # is_active queda en False hasta que la persona abre el enlace de activación (módulo 002).
    is_active = models.BooleanField(_("activo"), default=False)
    is_staff = models.BooleanField(_("acceso al panel de Django"), default=False)
    fecha_registro = models.DateTimeField(_("fecha de registro"), default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"  # el campo con el que se inicia sesión
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nombres", "apellidos"]  # los pide createsuperuser

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return self.nombre_completo or self.email

    def save(self, *args, **kwargs):
        """Guarda siempre el correo en minúsculas para que sea único sin importar mayúsculas."""
        self.email = UsuarioManager.normalizar_correo(self.email)
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def get_full_name(self):
        return self.nombre_completo

    def get_short_name(self):
        return self.nombres

    @property
    def es_estudiante(self):
        return self.rol == Rol.ESTUDIANTE

    @property
    def es_profesor(self):
        return self.rol == Rol.PROFESOR

    @property
    def es_admin(self):
        return self.rol == Rol.ADMIN
