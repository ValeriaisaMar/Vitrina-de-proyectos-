"""Registro del usuario en el panel de administración de Django."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from cuentas.forms import UsuarioCambioForm, UsuarioCreacionForm
from cuentas.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Permite buscar usuarios por correo o nombre y cambiar su rol."""

    form = UsuarioCambioForm
    add_form = UsuarioCreacionForm

    list_display = ("email", "nombres", "apellidos", "rol", "is_active", "fecha_registro")
    list_filter = ("rol", "is_active", "is_staff")
    search_fields = ("email", "nombres", "apellidos")
    ordering = ("apellidos", "nombres")
    readonly_fields = ("fecha_registro", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Datos personales"), {"fields": ("nombres", "apellidos")}),
        (_("Rol y acceso"), {"fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Fechas"), {"fields": ("fecha_registro", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nombres", "apellidos", "rol", "usable_password", "password1", "password2"),
        }),
    )
