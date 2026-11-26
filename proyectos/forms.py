"""Formulario para crear y editar proyectos."""

import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from config.texto import FormularioNFC
from cuentas.models import Rol
from proyectos.models import MAX_AUTORES, MAX_IMAGENES, MAX_TECNOLOGIAS, Asignatura, Estado, Imagen, Periodo, PlanEstudio, Proyecto, Tecnologia
from proyectos.paleta import COLOR_POR_DEFECTO, PALETA
from proyectos.validadores import validar_imagen

Usuario = get_user_model()
ROMANOS = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


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


# ---------------------------------------------------------------- Asignaturas por plan y semestre (spec 009)


def asignaturas_elegibles(conservar=()):
    """Asignaturas que se pueden elegir: activas de planes activos, más las indicadas en `conservar`.

    `conservar` son las que ya tiene el proyecto o el profesor: aunque las hayan desactivado, no
    desaparecen de su formulario (así no se pierden al guardar otra cosa).
    """
    conservar = [pk for pk in conservar if pk]
    consulta = Asignatura.objects.ofrecidas()
    if conservar:
        consulta = consulta | Asignatura.objects.filter(pk__in=conservar)
    return consulta.distinct().select_related("plan").order_by("-plan__anio", "plan__nombre", "semestre", "nombre")


def opciones_por_plan_y_semestre(asignaturas, vacio=True):
    """Opciones agrupadas para un <select>: «Plan 2022 · Semestre III» → asignaturas."""
    grupos = {}
    for asignatura in asignaturas:
        etiqueta = _("%(plan)s · Semestre %(n)s") % {"plan": asignatura.plan.nombre, "n": ROMANOS[asignatura.semestre]}
        texto = f"{asignatura.nombre} ({asignatura.codigo})" if asignatura.codigo else asignatura.nombre
        grupos.setdefault(etiqueta, []).append((asignatura.pk, texto))
    return ([("", "—")] if vacio else []) + list(grupos.items())


def configurar_selector_asignatura(campo, conservar=()):
    """Deja un campo de asignatura con las elegibles, agrupadas, y el buscador de selector.js."""
    asignaturas = asignaturas_elegibles(conservar)
    campo.queryset = asignaturas
    campo.widget.choices = opciones_por_plan_y_semestre(asignaturas, vacio=not getattr(campo.widget, "allow_multiple_selected", False))
    campo.widget.attrs["data-buscable"] = ""


# ---------------------------------------------------------------- Formulario principal


class FormularioProyecto(FormularioNFC, forms.ModelForm):
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
    # Spec 009, historia 7: la cara del proyecto. Se convierte a webp 16:9 en save().
    portada = forms.FileField(
        label=_("Imagen de portada"), required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        help_text=_("Opcional. JPG, PNG o WEBP de hasta 5 MB. Se recorta a 16:9 (1200 × 675). Es la cara del proyecto en la vitrina y al compartirlo."),
    )
    quitar_portada = forms.BooleanField(label=_("Quitar la portada y usar la portada de color"), required=False)

    class Meta:
        model = Proyecto
        # Sin "periodo": el proyecto toma el período actual al enviarse (spec 009)
        fields = ("titulo", "resumen", "descripcion", "asignatura", "tecnologias",
                  "repositorio", "demo", "video", "documento_pdf", "color_portada")
        widgets = {
            "resumen": forms.Textarea(attrs={"rows": 2, "maxlength": 300}),
            "descripcion": forms.Textarea(attrs={"rows": 8}),
            "tecnologias": forms.CheckboxSelectMultiple,
            "repositorio": forms.URLInput(attrs={"placeholder": "https://github.com/usuario/proyecto"}),
            "demo": forms.URLInput(attrs={"placeholder": "https://"}),
            "video": forms.URLInput(attrs={"placeholder": "https://www.youtube.com/watch?v=…"}),
            "color_portada": forms.RadioSelect,
            "documento_pdf": forms.ClearableFileInput(attrs={"accept": "application/pdf"}),
        }
        help_texts = {
            "repositorio": _("Enlace público a GitHub, GitLab u otro servicio."),
            "demo": _("Opcional. Donde se puede ver funcionando. Aparece como «Ver proyecto desplegado»."),
            "video": _("Opcional. YouTube u otro sitio. Se abre en una pestaña nueva; no se incrusta."),
            "color_portada": _("Se usa cuando el proyecto no tiene imagen de portada."),
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

        # Asignaturas activas de planes activos (más la actual, aunque la hayan desactivado),
        # agrupadas por plan y semestre (spec 009)
        tecnologias = Tecnologia.objects.filter(activa=True)
        if not es_nuevo:
            tecnologias = tecnologias | self.instance.tecnologias.all()
        self.fields["tecnologias"].queryset = tecnologias.distinct()
        configurar_selector_asignatura(self.fields["asignatura"], conservar=[self.instance.asignatura_id] if not es_nuevo else [])

        self.fields["tecnologias"].help_text = _("Elige entre 1 y 8.")

        self._portada_anterior = None if es_nuevo else self.instance.imagen_portada.name
        # Para dibujar la paleta con su muestra de color (clave, nombre, código)
        self.colores = [(clave, nombre, codigo) for clave, (nombre, codigo) in PALETA.items()]
        self.fields["color_portada"].required = False  # vacío: se conserva el color que tenía
        if es_nuevo or not self.instance.imagen_portada:
            del self.fields["quitar_portada"]
        if es_nuevo:
            del self.fields["quitar_imagenes"]
        else:
            self.fields["quitar_imagenes"].queryset = self.instance.imagenes.all()
            creador = self.instance.creador
            self.fields["coautores"].initial = "\n".join(
                a.email for a in self.instance.autores.all() if a != creador
            )
            if usuario != creador:
                # Solo el creador agrega o quita coautores; los demás autores ven la lista bloqueada
                self.fields["coautores"].disabled = True
                self.fields["coautores"].help_text = _("Solo quien creó el proyecto puede cambiar los coautores. Si quieres dejar el proyecto, usa «Salir del proyecto» en Mis proyectos.")

    # ------------------------------------------------------------ Validaciones

    def creador(self):
        """Quien creó el proyecto: el usuario actual si es nuevo; si no, el creador guardado."""
        return self._creador

    def clean_coautores(self):
        """Convierte la lista de correos en usuarios válidos o explica cuáles fallan."""
        if self.fields["coautores"].disabled:
            # Lista bloqueada: se conservan los coautores actuales tal como están
            return [a for a in self.instance.autores.all() if a != self._creador]
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
            # Debe TENER el rol estudiante (aunque además sea profesor o admin)
            usuario = Usuario.objects.filter(email__iexact=correo, is_active=True, roles_asignados__rol=Rol.ESTUDIANTE).first()
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

    def clean_color_portada(self):
        return self.cleaned_data.get("color_portada") or self.instance.color_portada or COLOR_POR_DEFECTO

    def clean_portada(self):
        from config.imagenes import validar_imagen_subida

        portada = self.cleaned_data.get("portada")
        if portada:
            validar_imagen_subida(portada)
        return portada

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
        self._guardar_portada(proyecto)
        self._borrar_pdf_reemplazado(proyecto)
        return proyecto

    def _guardar_portada(self, proyecto):
        """Nueva portada (webp 16:9 con nombre aleatorio) o quitarla; el archivo anterior se borra."""
        from config.imagenes import TAM_PORTADA, convertir_a_webp

        nueva = self.cleaned_data.get("portada")
        if nueva:
            contenido = convertir_a_webp(nueva, TAM_PORTADA)
            proyecto.imagen_portada.save(contenido.name, contenido, save=False)
        elif self.cleaned_data.get("quitar_portada"):
            proyecto.imagen_portada = ""
        else:
            return
        proyecto.save(update_fields=["imagen_portada"])
        if self._portada_anterior and self._portada_anterior != proyecto.imagen_portada.name:
            proyecto.imagen_portada.storage.delete(self._portada_anterior)

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


class FormularioTransferir(forms.Form):
    """El creador elige a cuál coautor le pasa el proyecto."""

    nuevo_creador = forms.ModelChoiceField(
        label=_("Nuevo creador"), queryset=Usuario.objects.none(), widget=forms.RadioSelect,
        empty_label=None, error_messages={"required": _("Elige a quién le pasas el proyecto.")},
    )

    def __init__(self, *args, proyecto, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nuevo_creador"].queryset = Usuario.objects.filter(
            autorias__proyecto=proyecto, autorias__es_creador=False, is_active=True,
        ).order_by("apellidos", "nombres")
        self.fields["nuevo_creador"].label_from_instance = lambda u: f"{u.nombre_completo} · {u.email}"


class FormularioEnvio(FormularioNFC, forms.Form):
    """Mensaje opcional del autor al enviar o reenviar el proyecto."""

    comentario = forms.CharField(
        label=_("Mensaje para el docente"), required=False, max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Opcional. Si lo reenvías, cuenta qué corregiste."),
    )


class FormularioDecision(FormularioNFC, forms.Form):
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


# ---------------------------------------------------------------- Periodos académicos (spec 008)


class FormularioPeriodo(forms.ModelForm):
    """El admin crea o edita un periodo académico."""

    class Meta:
        model = Periodo
        fields = ("nombre", "tipo", "fecha_inicio", "fecha_fin")
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "2026-2 · Intensivo noviembre 2026"}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
        help_texts = {
            "nombre": _("Como lo verán los estudiantes y la vitrina. Debe ser único."),
            "fecha_inicio": _("Sirve para ordenar los periodos del más reciente al más antiguo."),
            "fecha_fin": _("Opcional."),
        }

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        if Periodo.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Ya existe un periodo con ese nombre."))
        return nombre

    def save(self, commit=True):
        periodo = super().save(commit=False)
        if "nombre" in self.changed_data:
            periodo.slug = ""  # se recalcula con el nombre nuevo
        if commit:
            periodo.save()
        return periodo


# ---------------------------------------------------------------- Plan de estudios (spec 009, historia 3)


class FormularioPlan(FormularioNFC, forms.ModelForm):
    """El admin crea o edita un plan de estudios."""

    class Meta:
        model = PlanEstudio
        fields = ("nombre", "anio", "activo")
        widgets = {"nombre": forms.TextInput(attrs={"placeholder": "Plan 2026"})}
        help_texts = {"activo": _("Solo las asignaturas de planes activos se ofrecen en los formularios.")}

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        if PlanEstudio.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Ya existe un plan con ese nombre."))
        return nombre


class FormularioAsignatura(FormularioNFC, forms.ModelForm):
    """El admin crea o edita una asignatura dentro de un plan."""

    class Meta:
        model = Asignatura
        fields = ("nombre", "codigo", "semestre", "activa")
        widgets = {"codigo": forms.TextInput(attrs={"placeholder": "ISW-301"})}
        help_texts = {"codigo": _("Opcional."), "activa": _("Una asignatura inactiva no se ofrece en los formularios, pero la conservan quienes ya la tienen.")}

    def __init__(self, *args, plan, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = plan
        self.fields["semestre"].widget = forms.Select(choices=[(n, _("Semestre %(n)s") % {"n": ROMANOS[n]}) for n in range(1, 11)])

    def clean_nombre(self):
        """Sin repetir dentro del plan, sin distinguir mayúsculas ni espacios de más."""
        nombre = " ".join(self.cleaned_data["nombre"].split())
        if Asignatura.objects.filter(plan=self.plan, nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Ya existe una asignatura con ese nombre en este plan."))
        return nombre

    def save(self, commit=True):
        asignatura = super().save(commit=False)
        asignatura.plan = self.plan
        if commit:
            asignatura.save()
        return asignatura


# ---------------------------------------------------------------- Revisor elegido (spec 009, historia 5)


class _ProfesorField(forms.ModelChoiceField):
    def label_from_instance(self, usuario):
        return usuario.nombre_completo


class FormularioElegirProfesor(forms.Form):
    """El creador elige al profesor que revisará su proyecto (las tarjetas se dibujan a mano)."""

    profesor = _ProfesorField(
        label=_("Profesor"), queryset=Usuario.objects.none(), widget=forms.RadioSelect,
        error_messages={"required": _("Elige quién revisará tu proyecto."), "invalid_choice": _("No puedes elegir a ese profesor.")},
    )

    def __init__(self, *args, elegibles, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profesor"].queryset = elegibles


class FormularioNoAceptar(FormularioNFC, forms.Form):
    """El profesor no acepta la solicitud: mensaje y recomendación opcionales."""

    mensaje = forms.CharField(
        label=_("Mensaje para los estudiantes"), required=False, max_length=1000,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text=_("Opcional. Por ejemplo, por qué no puedes revisarlo ahora."),
    )
    recomendado = _ProfesorField(label=_("Recomendar a otro profesor"), queryset=Usuario.objects.none(), required=False, empty_label=_("Sin recomendación"))

    def __init__(self, *args, elegibles, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recomendado"].queryset = elegibles


class FormularioReasignar(FormularioNFC, forms.Form):
    """El admin asigna otro profesor revisor."""

    profesor = _ProfesorField(label=_("Nuevo profesor revisor"), queryset=Usuario.objects.none())
    motivo = forms.CharField(label=_("Motivo"), required=False, max_length=500, widget=forms.Textarea(attrs={"rows": 2}),
                             help_text=_("Opcional. Queda en el historial del proyecto."))

    def __init__(self, *args, elegibles, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profesor"].queryset = elegibles
