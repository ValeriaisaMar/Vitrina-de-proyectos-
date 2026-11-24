"""Formulario de búsqueda y filtros de la página Explorar (se envía por GET)."""

from django import forms
from django.utils.translation import gettext_lazy as _

from proyectos.models import Asignatura, Proyecto, Tecnologia

ORDENES = [("recientes", _("Más recientes")), ("titulo", _("Nombre (A–Z)"))]


class FormularioFiltros(forms.Form):
    q = forms.CharField(label=_("Buscar"), required=False, max_length=100)
    tecnologia = forms.ModelMultipleChoiceField(
        label=_("Tecnología"), queryset=Tecnologia.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    asignatura = forms.ModelChoiceField(label=_("Asignatura"), queryset=Asignatura.objects.none(), required=False, empty_label=_("Todas"))
    periodo = forms.ChoiceField(label=_("Periodo"), required=False)
    orden = forms.ChoiceField(label=_("Ordenar"), choices=ORDENES, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        publicados = Proyecto.objects.publicados()
        # Solo se ofrecen asignaturas y periodos que tienen proyectos publicados
        self.fields["asignatura"].queryset = Asignatura.objects.filter(proyectos__in=publicados).distinct()
        periodos = publicados.order_by("-periodo").values_list("periodo", flat=True).distinct()
        self.fields["periodo"].choices = [("", _("Todos"))] + [(p, p) for p in periodos]

    def filtrar(self, consulta):
        """Aplica a la consulta los filtros que pasaron la validación; los inválidos se ignoran."""
        from django.db.models import Q

        datos = self.cleaned_data if self.is_bound and self.is_valid() else getattr(self, "cleaned_data", {})
        if texto := (datos.get("q") or "").strip():
            consulta = consulta.filter(
                Q(titulo__icontains=texto) | Q(resumen__icontains=texto)
                | Q(tecnologias__nombre__icontains=texto)
                | Q(autores__nombres__icontains=texto) | Q(autores__apellidos__icontains=texto)
            )
        if tecnologias := datos.get("tecnologia"):
            consulta = consulta.filter(tecnologias__in=tecnologias)
        if asignatura := datos.get("asignatura"):
            consulta = consulta.filter(asignatura=asignatura)
        if periodo := datos.get("periodo"):
            consulta = consulta.filter(periodo=periodo)

        consulta = consulta.distinct()
        if datos.get("orden") == "titulo":
            return consulta.order_by("titulo")
        return consulta.order_by("-aprobado_en", "-actualizado_en")
