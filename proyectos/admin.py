"""Panel de Django para asignaturas, tecnologías y proyectos.

El estado, el revisor, el código y la fecha de aprobación son de solo lectura: solo los cambia
proyectos/servicios.py (constitución, principios VI y VII). Para revisar un proyecto se usa la
bandeja de la web. El historial se ve aquí, pero no se puede editar ni borrar.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from proyectos.models import Asignatura, Autoria, Consecutivo, Estado, EventoEstado, Imagen, Periodo, Proyecto, Tecnologia


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "semestre", "activa")
    list_filter = ("semestre", "activa")
    list_editable = ("activa",)
    search_fields = ("nombre",)


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    """También se gestionan desde la app (Mi panel → Periodos)."""

    list_display = ("nombre", "tipo", "fecha_inicio", "fecha_fin", "abierto")
    list_filter = ("tipo", "abierto")
    list_editable = ("abierto",)
    search_fields = ("nombre",)


@admin.register(Tecnologia)
class TecnologiaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_editable = ("activa",)
    search_fields = ("nombre",)


class AutoriaEnLinea(admin.TabularInline):
    model = Autoria
    extra = 0
    autocomplete_fields = ("usuario",)


class ImagenEnLinea(admin.TabularInline):
    model = Imagen
    extra = 0


class SoloLectura:
    """Mezcla para que un modelo se pueda ver en el admin pero no crear, editar ni borrar."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class EventoEnLinea(SoloLectura, admin.TabularInline):
    model = EventoEstado
    extra = 0
    fields = ("creado_en", "estado_anterior", "estado_nuevo", "actor", "comentario")
    readonly_fields = fields
    verbose_name_plural = _("historial de estados")


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "estado", "asignatura", "periodo", "actualizado_en")
    list_filter = ("estado", "periodo", "asignatura__semestre")
    list_select_related = ("asignatura", "periodo")
    search_fields = ("titulo", "resumen", "autores__email", "autores__nombres", "autores__apellidos")
    readonly_fields = ("slug", "estado", "revisor", "codigo", "aprobado_en", "creado_en", "actualizado_en")
    filter_horizontal = ("tecnologias",)
    inlines = [AutoriaEnLinea, ImagenEnLinea, EventoEnLinea]

    def has_delete_permission(self, request, obj=None):
        """Un proyecto que ya salió de Borrador no se borra (constitución, principio VII)."""
        if obj is not None and obj.estado != Estado.BORRADOR:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        # La acción "borrar seleccionados" se salta has_delete_permission(obj) por cada proyecto
        acciones = super().get_actions(request)
        acciones.pop("delete_selected", None)
        return acciones


@admin.register(EventoEstado)
class EventoEstadoAdmin(SoloLectura, admin.ModelAdmin):
    list_display = ("creado_en", "proyecto", "estado_anterior", "estado_nuevo", "actor")
    list_filter = ("estado_nuevo",)
    search_fields = ("proyecto__titulo", "actor__email", "comentario")
    date_hierarchy = "creado_en"


@admin.register(Consecutivo)
class ConsecutivoAdmin(SoloLectura, admin.ModelAdmin):
    list_display = ("anio", "ultimo")
