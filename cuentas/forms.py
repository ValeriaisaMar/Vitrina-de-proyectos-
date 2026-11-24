"""Formularios del panel de administración para el usuario propio.

Los formularios de Django vienen pensados para un usuario con "username"; aquí se adaptan
para que usen el correo, los nombres y los apellidos.
"""

from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from cuentas.models import Usuario


class UsuarioCreacionForm(AdminUserCreationForm):
    """Crear un usuario desde el admin."""

    class Meta:
        model = Usuario
        fields = ("email", "nombres", "apellidos", "rol")


class UsuarioCambioForm(UserChangeForm):
    """Editar un usuario desde el admin."""

    class Meta:
        model = Usuario
        fields = ("email", "nombres", "apellidos", "rol", "is_active", "is_staff")
