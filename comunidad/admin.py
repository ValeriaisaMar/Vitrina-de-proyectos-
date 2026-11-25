"""Comentarios en el panel de Django, con acciones para ocultar y mostrar."""

from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from comunidad.models import Comentario


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "proyecto", "autor", "texto", "oculto")
    list_filter = ("oculto",)
    search_fields = ("texto", "autor__email", "proyecto__titulo")
    readonly_fields = ("proyecto", "autor", "texto", "creado_en", "ocultado_por", "ocultado_en")
    fields = readonly_fields[:4] + ("oculto",) + readonly_fields[4:]
    actions = ["ocultar", "mostrar"]

    def save_model(self, request, obj, form, change):
        if "oculto" in form.changed_data:
            obj.ocultado_por = request.user if obj.oculto else None
            obj.ocultado_en = timezone.now() if obj.oculto else None
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Ocultar los comentarios seleccionados"))
    def ocultar(self, request, queryset):
        queryset.update(oculto=True, ocultado_por=request.user, ocultado_en=timezone.now())

    @admin.action(description=_("Mostrar los comentarios seleccionados"))
    def mostrar(self, request, queryset):
        queryset.update(oculto=False, ocultado_por=None, ocultado_en=None)
