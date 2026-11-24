"""Panel de Django para asignaturas, tecnologías y proyectos."""

from django.contrib import admin

from proyectos.models import Asignatura, Autoria, Imagen, Proyecto, Tecnologia


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "semestre", "activa")
    list_filter = ("semestre", "activa")
    list_editable = ("activa",)
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


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "estado", "asignatura", "periodo", "actualizado_en")
    list_filter = ("estado", "periodo", "asignatura__semestre")
    search_fields = ("titulo", "resumen", "autores__email", "autores__nombres", "autores__apellidos")
    readonly_fields = ("slug", "creado_en", "actualizado_en")
    filter_horizontal = ("tecnologias",)
    inlines = [AutoriaEnLinea, ImagenEnLinea]
