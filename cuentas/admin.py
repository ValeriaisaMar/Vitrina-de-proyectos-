"""Registro del usuario en el panel de administración de Django."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from cuentas.forms import UsuarioCambioForm, UsuarioCreacionForm
from cuentas.models import CambioRol, Rol, RolAsignado, Usuario


class RolAsignadoEnLinea(admin.TabularInline):
    """Los roles de la persona, en la misma página del usuario."""

    model = RolAsignado
    fk_name = "usuario"
    extra = 0
    fields = ("rol", "asignado_por", "asignado_en")
    readonly_fields = ("asignado_por", "asignado_en")


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Permite buscar usuarios por correo o nombre y cambiar sus roles."""

    form = UsuarioCambioForm
    add_form = UsuarioCreacionForm
    inlines = [RolAsignadoEnLinea]

    list_display = ("email", "nombres", "apellidos", "lista_roles", "is_active", "fecha_registro")
    list_filter = ("roles_asignados__rol", "is_active", "is_staff")
    search_fields = ("email", "nombres", "apellidos")
    ordering = ("apellidos", "nombres")
    readonly_fields = ("fecha_registro", "last_login", "ultimo_rol")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Datos personales"), {"fields": ("nombres", "apellidos")}),
        (_("Acceso"), {"fields": ("is_active", "is_staff", "is_superuser", "ultimo_rol", "groups", "user_permissions")}),
        (_("Fechas"), {"fields": ("fecha_registro", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "nombres", "apellidos", "usable_password", "password1", "password2"),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("roles_asignados")

    @admin.display(description=_("roles"))
    def lista_roles(self, usuario):
        return ", ".join(str(Rol(r).label) for r in usuario.roles)

    def save_related(self, request, form, formsets, change):
        """Toda cuenta necesita al menos un rol: si quedó sin ninguno, recibe el de estudiante."""
        super().save_related(request, form, formsets, change)
        usuario = form.instance
        usuario.olvidar_roles()
        if not usuario.roles:
            RolAsignado.objects.create(usuario=usuario, rol=Rol.ESTUDIANTE, asignado_por=request.user)


@admin.register(CambioRol)
class CambioRolAdmin(admin.ModelAdmin):
    """Registro de roles dados y quitados. Solo lectura."""

    list_display = ("fecha", "usuario", "rol", "accion", "hecho_por")
    list_filter = ("rol", "accion")
    search_fields = ("usuario__email", "hecho_por__email")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
