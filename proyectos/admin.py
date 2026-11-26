"""Panel de Django para asignaturas, tecnologías y proyectos.

El estado, el revisor, el código y la fecha de aprobación son de solo lectura: solo los cambia
proyectos/servicios.py (constitución, principios VI y VII). Para revisar un proyecto se usa la
bandeja de la web. El historial se ve aquí, pero no se puede editar ni borrar.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from proyectos.models import Asignatura, Autoria, Consecutivo, Estado, EventoEstado, Imagen, Periodo, PlanEstudio, Proyecto, SolicitudRevision, Tecnologia


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    """También se gestionan desde la app (Mi panel → Plan de estudios)."""

    list_display = ("nombre", "codigo", "plan", "semestre", "activa")
    list_filter = ("plan", "semestre", "activa")
    list_editable = ("activa",)
    list_select_related = ("plan",)
    search_fields = ("nombre", "codigo")


@admin.register(PlanEstudio)
class PlanEstudioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "anio", "activo")
    list_editable = ("activo",)


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    """También se gestionan desde la app (Mi panel → Periodos)."""

    list_display = ("nombre", "tipo", "fecha_inicio", "fecha_fin", "es_actual")
    list_filter = ("tipo", "es_actual")
    # es_actual no se edita aquí: el cambio lo hace la app (Periodos → Marcar como período actual),
    # que desmarca el anterior en la misma transacción.
    readonly_fields = ("es_actual",)
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


@admin.register(SolicitudRevision)
class SolicitudRevisionAdmin(admin.ModelAdmin):
    """Solicitudes de revisión (spec 009). Solo lectura: se crean y responden desde la app."""

    list_display = ("proyecto", "profesor", "estado", "creada_en", "respondida_en")
    list_filter = ("estado",)
    list_select_related = ("proyecto", "profesor")
    search_fields = ("proyecto__titulo", "profesor__email", "profesor__apellidos")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
