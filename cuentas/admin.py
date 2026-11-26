"""Registro del usuario en el panel de administración de Django."""

from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from cuentas.forms import UsuarioCambioForm, UsuarioCreacionForm
from cuentas.models import Aptitud, CambioRol, Estudio, ExperienciaLaboral, Perfil, Rol, RolAsignado, Usuario
from cuentas.roles import es_ultimo_admin


def hay_admin_activo_sin(usuarios):
    """True si queda al menos una cuenta admin activa fuera de las indicadas."""
    return Usuario.objects.filter(is_active=True, roles_asignados__rol=Rol.ADMIN).exclude(pk__in=usuarios).exists()


class RolesEnLineaFormSet(BaseInlineFormSet):
    """No deja quitarle (o cambiarle) el rol admin a la única cuenta admin activa (spec 010)."""

    def clean(self):
        super().clean()
        if self.instance.pk is None or not es_ultimo_admin(self.instance):
            return
        queda_admin = any(
            form.cleaned_data.get("rol") == Rol.ADMIN and not form.cleaned_data.get("DELETE")
            for form in self.forms if hasattr(form, "cleaned_data")
        )
        if not queda_admin:
            raise ValidationError(
                _("No puedes quitarle el rol admin: es la única cuenta admin activa. Primero nombra a otro admin."),
            )


@admin.action(permissions=["delete"], description=_("Eliminar los usuarios seleccionados"))
def eliminar_seleccionados(modeladmin, request, queryset):
    """La acción "eliminar" de Django, pero sin dejar la plataforma sin admins activos (spec 010)."""
    hay_admins = Usuario.objects.filter(is_active=True, roles_asignados__rol=Rol.ADMIN).exists()
    if hay_admins and not hay_admin_activo_sin(queryset.values("pk")):
        modeladmin.message_user(
            request, _("No se eliminó nada: entre los seleccionados está la única cuenta admin activa."),
            messages.ERROR,
        )
        return None
    return delete_selected(modeladmin, request, queryset)


class RolAsignadoEnLinea(admin.TabularInline):
    """Los roles de la persona, en la misma página del usuario."""

    model = RolAsignado
    formset = RolesEnLineaFormSet
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

    def get_actions(self, request):
        """Cambia la acción "eliminar" por la que protege al último admin."""
        acciones = super().get_actions(request)
        if "delete_selected" in acciones:
            acciones["delete_selected"] = (eliminar_seleccionados, "delete_selected", eliminar_seleccionados.short_description)
        return acciones

    def has_delete_permission(self, request, obj=None):
        """La única cuenta admin activa no se puede eliminar (spec 010)."""
        if obj is not None and es_ultimo_admin(obj):
            return False
        return super().has_delete_permission(request, obj)

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

    list_display = ("fecha", "usuario", "rol", "accion", "hecho_por", "motivo")
    list_filter = ("rol", "accion")
    search_fields = ("usuario__email", "hecho_por__email")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Aptitud)
class AptitudAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


class ExperienciaEnLinea(admin.TabularInline):
    model = ExperienciaLaboral
    extra = 0


class EstudioEnLinea(admin.TabularInline):
    model = Estudio
    extra = 0


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    """Perfil público (spec 009). Cada persona edita el suyo desde su página."""

    list_display = ("usuario", "slug", "recibiendo_proyectos", "bienvenida_vista")
    list_select_related = ("usuario",)
    search_fields = ("usuario__email", "usuario__nombres", "usuario__apellidos", "slug")
    readonly_fields = ("slug",)
    filter_horizontal = ("aptitudes", "asignaturas_imparte")
    inlines = [ExperienciaEnLinea, EstudioEnLinea]
