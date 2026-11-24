"""Formulario para crear y editar proyectos."""

import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cuentas.models import Rol
from proyectos.models import MAX_AUTORES, MAX_IMAGENES, MAX_TECNOLOGIAS, Asignatura, Estado, Imagen, Proyecto, Tecnologia
from proyectos.validadores import validar_imagen

Usuario = get_user_model()
ROMANOS = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def opciones_de_periodo(desde=2020):
    """Periodos académicos desde 2020 hasta el año siguiente, del más reciente al más antiguo."""
    hasta = timezone.now().year + 1
    return [(f"{a}-{s}", f"{a}-{s}") for a in range(hasta, desde - 1, -1) for s in (2, 1)]


# ---------------------------------------------------------------- Varias imágenes en un campo
# Patrón recomendado por la documentación de Django para subir varios archivos con un input.


class VariosArchivosInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class VariasImagenesField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", VariosArchivosInput(attrs={"accept": "image/jpeg,image/png,image/webp"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        limpiar_una = super().clean
        if isinstance(data, (list, tuple)):
            return [limpiar_una(archivo, initial) for archivo in data if archivo]
        return [limpiar_una(data, initial)] if data else []


# ---------------------------------------------------------------- Formulario principal


class FormularioProyecto(forms.ModelForm):
    """Crea o edita un proyecto. Recibe el usuario que lo usa para saber quién es el creador."""

    coautores = forms.CharField(
        label=_("Coautores"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "companera@correo.com\ncompanero@correo.com"}),
        help_text=_("Correos de otros estudiantes con cuenta activa, uno por línea o separados por comas. Máximo 5."),
    )
    imagenes = VariasImagenesField(
        label=_("Agregar imágenes"),
        required=False,
        help_text=_("Hasta 4 imágenes en total, JPG, PNG o WEBP de hasta 3 MB cada una."),
    )
    quitar_imagenes = forms.ModelMultipleChoiceField(
        label=_("Quitar imágenes"), queryset=Imagen.objects.none(), required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Proyecto
        fields = ("titulo", "resumen", "descripcion", "asignatura", "periodo", "tecnologias",
                  "repositorio", "demo", "documento_pdf")
        widgets = {
            "resumen": forms.Textarea(attrs={"rows": 2, "maxlength": 300}),
            "descripcion": forms.Textarea(attrs={"rows": 8}),
            "tecnologias": forms.CheckboxSelectMultiple,
            "periodo": forms.Select,
            "repositorio": forms.URLInput(attrs={"placeholder": "https://github.com/usuario/proyecto"}),
            "demo": forms.URLInput(attrs={"placeholder": "https://"}),
            "documento_pdf": forms.ClearableFileInput(attrs={"accept": "application/pdf"}),
        }
        help_texts = {
            "repositorio": _("Enlace público a GitHub, GitLab u otro servicio."),
            "demo": _("Opcional. Donde se puede probar el proyecto."),
            "documento_pdf": _("Opcional. Informe o manual del proyecto, PDF de hasta 10 MB."),
        }

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        es_nuevo = self.instance.pk is None
        # Se decide aquí, antes de guardar: después de save() el proyecto ya tiene pk
        # y todavía no tiene autores, así que no se podría preguntar quién es el creador.
        self._creador = usuario if es_nuevo else self.instance.creador
        self._pdf_anterior = None if es_nuevo else self.instance.documento_pdf.name

        # Asignaturas activas (más la actual, aunque la hayan desactivado), agrupadas por semestre
        asignaturas = Asignatura.objects.filter(activa=True)
        tecnologias = Tecnologia.objects.filter(activa=True)
        if not es_nuevo:
            asignaturas = asignaturas | Asignatura.objects.filter(pk=self.instance.asignatura_id)
            tecnologias = tecnologias | self.instance.tecnologias.all()
        self.fields["asignatura"].queryset = asignaturas.distinct()
        self.fields["tecnologias"].queryset = tecnologias.distinct()
        self.fields["asignatura"].widget.choices = self._asignaturas_por_semestre(asignaturas.distinct())

        self.fields["periodo"].widget.choices = [("", "—")] + opciones_de_periodo()
        self.fields["tecnologias"].help_text = _("Elige entre 1 y 8.")

        if es_nuevo:
            del self.fields["quitar_imagenes"]
        else:
            self.fields["quitar_imagenes"].queryset = self.instance.imagenes.all()
            creador = self.instance.creador
            self.fields["coautores"].initial = "\n".join(
                a.email for a in self.instance.autores.all() if a != creador
            )

    @staticmethod
    def _asignaturas_por_semestre(asignaturas):
        grupos = {}
        for asignatura in asignaturas.order_by("semestre", "nombre"):
            etiqueta = _("Semestre %(n)s") % {"n": ROMANOS[asignatura.semestre]}
            grupos.setdefault(etiqueta, []).append((asignatura.pk, asignatura.nombre))
        return [("", "—")] + list(grupos.items())

    # ------------------------------------------------------------ Validaciones

    def creador(self):
        """Quien creó el proyecto: el usuario actual si es nuevo; si no, el creador guardado."""
        return self._creador

    def clean_coautores(self):
        """Convierte la lista de correos en usuarios válidos o explica cuáles fallan."""
        texto = self.cleaned_data.get("coautores", "")
        correos = []
        for parte in re.split(r"[\s,;]+", texto):
            correo = parte.strip().lower()
            if correo and correo not in correos:
                correos.append(correo)

        creador = self.creador()
        correos = [c for c in correos if c != creador.email]

        invalidos, sin_cuenta, coautores = [], [], []
        for correo in correos:
            try:
                validate_email(correo)
            except ValidationError:
                invalidos.append(correo)
                continue
            usuario = Usuario.objects.filter(email__iexact=correo, is_active=True, rol=Rol.ESTUDIANTE).first()
            if usuario is None:
                sin_cuenta.append(correo)
            else:
                coautores.append(usuario)

        errores = []
        if invalidos:
            errores.append(_("Estos correos no son válidos: %(lista)s.") % {"lista": ", ".join(invalidos)})
        if sin_cuenta:
            errores.append(_("Estos correos no tienen una cuenta activa de estudiante: %(lista)s.") % {"lista": ", ".join(sin_cuenta)})
        if len(coautores) + 1 > MAX_AUTORES:
            errores.append(_("Un proyecto puede tener como máximo %(n)s autores.") % {"n": MAX_AUTORES})
        if errores:
            raise ValidationError(errores)
        return coautores

    def clean_tecnologias(self):
        tecnologias = self.cleaned_data.get("tecnologias")
        if tecnologias is not None and len(tecnologias) > MAX_TECNOLOGIAS:
            raise ValidationError(_("Elige como máximo %(n)s tecnologías.") % {"n": MAX_TECNOLOGIAS})
        return tecnologias

    def clean_imagenes(self):
        imagenes = self.cleaned_data.get("imagenes") or []
        errores = []
        for imagen in imagenes:
            try:
                validar_imagen(imagen)
            except ValidationError as error:
                errores.extend(error.messages)
        if errores:
            raise ValidationError(errores)
        return imagenes

    def clean(self):
        datos = super().clean()
        actuales = self.instance.imagenes.count() if self.instance.pk else 0
        quitadas = len(datos.get("quitar_imagenes") or [])
        nuevas = len(datos.get("imagenes") or [])
        if actuales - quitadas + nuevas > MAX_IMAGENES:
            self.add_error("imagenes", _("El proyecto puede tener como máximo %(n)s imágenes.") % {"n": MAX_IMAGENES})
        return datos

    # ------------------------------------------------------------ Guardado

    def save(self, commit=True):
        """Guarda el proyecto, sus autores e imágenes. La vista lo llama dentro de una transacción."""
        proyecto = super().save(commit=False)
        proyecto.save()
        self.save_m2m()  # tecnologías

        self._guardar_autores(proyecto)
        self._guardar_imagenes(proyecto)
        self._borrar_pdf_reemplazado(proyecto)
        return proyecto

    def _guardar_autores(self, proyecto):
        from proyectos.models import Autoria

        creador = self.creador()
        Autoria.objects.get_or_create(proyecto=proyecto, usuario=creador, defaults={"es_creador": True})
        coautores = self.cleaned_data.get("coautores", [])
        proyecto.autorias.exclude(usuario=creador).exclude(usuario__in=coautores).delete()
        for usuario in coautores:
            Autoria.objects.get_or_create(proyecto=proyecto, usuario=usuario)

    def _guardar_imagenes(self, proyecto):
        for imagen in self.cleaned_data.get("quitar_imagenes") or []:
            imagen.archivo.delete(save=False)
            imagen.delete()
        siguiente = (proyecto.imagenes.order_by("-orden").values_list("orden", flat=True).first() or 0) + 1
        for posicion, archivo in enumerate(self.cleaned_data.get("imagenes") or []):
            Imagen.objects.create(proyecto=proyecto, archivo=archivo, orden=siguiente + posicion)

    def _borrar_pdf_reemplazado(self, proyecto):
        """Si se cambió o se quitó el PDF, borra el archivo anterior del disco."""
        if self._pdf_anterior and self._pdf_anterior != proyecto.documento_pdf.name:
            proyecto.documento_pdf.storage.delete(self._pdf_anterior)


# ---------------------------------------------------------------- Revisión (módulo 004)


class FormularioEnvio(forms.Form):
    """Mensaje opcional del autor al enviar o reenviar el proyecto."""

    comentario = forms.CharField(
        label=_("Mensaje para el docente"), required=False, max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Opcional. Si lo reenvías, cuenta qué corregiste."),
    )


class FormularioDecision(forms.Form):
    """Decisión del docente sobre un proyecto en revisión."""

    decision = forms.ChoiceField(
        label=_("Decisión"),
        choices=[
            (Estado.APROBADO, _("Aprobar")),
            (Estado.CON_OBSERVACIONES, _("Pedir cambios")),
            (Estado.RECHAZADO, _("Rechazar")),
        ],
        widget=forms.RadioSelect,
    )
    comentario = forms.CharField(
        label=_("Comentario para los autores"), required=False, max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text=_("Obligatorio si pides cambios o rechazas. Los autores lo reciben por correo."),
    )

    def clean(self):
        datos = super().clean()
        if datos.get("decision") in (Estado.CON_OBSERVACIONES, Estado.RECHAZADO) and not datos.get("comentario", "").strip():
            self.add_error("comentario", _("Escribe un comentario para explicar la decisión."))
        return datos
