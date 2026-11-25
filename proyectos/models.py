"""Modelos de la app proyectos.

- Asignatura y Tecnologia: catálogos que administra el admin.
- Periodo: periodos académicos (ordinarios, intersemestrales, intensivos…) que crea el admin.
- Proyecto: el trabajo de uno o varios estudiantes.
- Autoria: une a cada autor con su proyecto y marca al creador.
- Imagen: capturas de la galería del proyecto.
- EventoEstado: historial de cambios de estado; nunca se edita ni se borra.
- Consecutivo: contador por año para los códigos VP-AAAA-NNNN.

Los campos estado, revisor, codigo y aprobado_en solo los cambia proyectos/servicios.py.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from proyectos.validadores import validar_imagen, validar_pdf, validar_url_web

MAX_AUTORES = 6
MAX_IMAGENES = 4
MAX_TECNOLOGIAS = 8


# --------------------------------------------------------------------------- Catálogos


class Asignatura(models.Model):
    """Asignatura de la malla de Ingeniería de Software."""

    nombre = models.CharField(_("nombre"), max_length=120, unique=True)
    semestre = models.PositiveSmallIntegerField(
        _("semestre"), validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    activa = models.BooleanField(_("activa"), default=True)

    class Meta:
        verbose_name = _("asignatura")
        verbose_name_plural = _("asignaturas")
        ordering = ["semestre", "nombre"]

    def __str__(self):
        return self.nombre


class Tecnologia(models.Model):
    """Lenguaje, framework o herramienta usada en un proyecto (Django, Flutter…)."""

    nombre = models.CharField(_("nombre"), max_length=60, unique=True)
    activa = models.BooleanField(_("activa"), default=True)

    class Meta:
        verbose_name = _("tecnología")
        verbose_name_plural = _("tecnologías")
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class TipoPeriodo(models.TextChoices):
    ORDINARIO = "ordinario", _("Ordinario")
    INTERSEMESTRAL = "intersemestral", _("Intersemestral")
    INTENSIVO = "intensivo", _("Intensivo")
    OTRO = "otro", _("Otro")


class PeriodoQuerySet(models.QuerySet):
    def abiertos(self):
        """Periodos en los que los estudiantes pueden registrar proyectos."""
        return self.filter(abierto=True)


class Periodo(models.Model):
    """Periodo académico (spec 008, historia 2). Lo crea y lo abre o cierra el admin desde la app.

    El nombre es libre ("2026-2", "Intensivo noviembre 2026"); la fecha de inicio sirve para
    ordenar del más reciente al más antiguo. Un periodo con proyectos no se borra: se cierra.
    """

    nombre = models.CharField(_("nombre"), max_length=60, unique=True)
    slug = models.SlugField(_("dirección"), max_length=70, unique=True, editable=False)
    tipo = models.CharField(_("tipo"), max_length=15, choices=TipoPeriodo.choices, default=TipoPeriodo.ORDINARIO)
    fecha_inicio = models.DateField(_("fecha de inicio"))
    fecha_fin = models.DateField(_("fecha de fin"), null=True, blank=True)
    abierto = models.BooleanField(
        _("abierto para entregas"), default=True,
        help_text=_("Si está abierto, los estudiantes pueden elegirlo al registrar un proyecto."),
    )

    objects = PeriodoQuerySet.as_manager()

    class Meta:
        verbose_name = _("periodo académico")
        verbose_name_plural = _("periodos académicos")
        ordering = ["-fecha_inicio", "-id"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._slug_unico()
        super().save(*args, **kwargs)

    def _slug_unico(self):
        base = slugify(self.nombre)[:60] or "periodo"
        slug, n = base, 2
        while Periodo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug, n = f"{base}-{n}", n + 1
        return slug

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({"fecha_fin": _("La fecha de fin no puede ser anterior a la de inicio.")})


# --------------------------------------------------------------------------- Proyecto


class Estado(models.TextChoices):
    """Estados del proyecto (constitución, principio VII). Solo los cambia servicios.cambiar_estado."""

    BORRADOR = "borrador", _("Borrador")
    ENVIADO = "enviado", _("Enviado")
    EN_REVISION = "en_revision", _("En revisión")
    CON_OBSERVACIONES = "con_observaciones", _("Con observaciones")
    APROBADO = "aprobado", _("Aprobado")
    RECHAZADO = "rechazado", _("Rechazado")


ESTADOS_EDITABLES = {Estado.BORRADOR, Estado.CON_OBSERVACIONES}
ESTADOS_DE_DECISION = {Estado.APROBADO, Estado.CON_OBSERVACIONES, Estado.RECHAZADO}


def ruta_documento(instancia, nombre_original):
    """Guarda el PDF con un nombre aleatorio para no exponer ni pisar nombres de archivo."""
    return f"proyectos/documentos/{uuid.uuid4().hex}.pdf"


def ruta_imagen(instancia, nombre_original):
    return f"proyectos/imagenes/{uuid.uuid4().hex}{Path(nombre_original).suffix.lower()}"


class ProyectoQuerySet(models.QuerySet):
    def publicados(self):
        """Los únicos proyectos que pueden mostrarse en páginas públicas (constitución, VI)."""
        return self.filter(estado=Estado.APROBADO)

    def de_autor(self, usuario):
        return self.filter(autores=usuario)

    def con_relaciones(self):
        """Trae asignatura, tecnologías, autores e imágenes sin consultas extra por proyecto."""
        return self.select_related("asignatura", "periodo").prefetch_related("tecnologias", "autores", "imagenes")


class Proyecto(models.Model):
    titulo = models.CharField(_("título"), max_length=120)
    slug = models.SlugField(_("dirección"), max_length=140, unique=True, editable=False)
    resumen = models.CharField(_("resumen"), max_length=300, help_text=_("Una o dos frases. Aparece en las tarjetas."))
    descripcion = models.TextField(_("descripción"))
    asignatura = models.ForeignKey(Asignatura, verbose_name=_("asignatura"), on_delete=models.PROTECT, related_name="proyectos")
    periodo = models.ForeignKey(Periodo, verbose_name=_("periodo"), on_delete=models.PROTECT, related_name="proyectos")
    tecnologias = models.ManyToManyField(Tecnologia, verbose_name=_("tecnologías"), related_name="proyectos")
    repositorio = models.URLField(_("repositorio"), validators=[validar_url_web])
    demo = models.URLField(_("demo en línea"), blank=True, validators=[validar_url_web])
    documento_pdf = models.FileField(_("documento PDF"), upload_to=ruta_documento, blank=True, validators=[validar_pdf])

    autores = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Autoria", related_name="proyectos", verbose_name=_("autores"))
    estado = models.CharField(_("estado"), max_length=20, choices=Estado.choices, default=Estado.BORRADOR, db_index=True)

    # Los llena servicios.cambiar_estado: revisor al tomar, codigo y aprobado_en al aprobar
    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("revisor"), on_delete=models.SET_NULL,
        null=True, blank=True, related_name="proyectos_revisados",
    )
    codigo = models.CharField(_("código de verificación"), max_length=12, unique=True, null=True, blank=True)
    aprobado_en = models.DateTimeField(_("aprobado en"), null=True, blank=True)

    creado_en = models.DateTimeField(_("creado en"), auto_now_add=True)
    actualizado_en = models.DateTimeField(_("actualizado en"), auto_now=True)

    objects = ProyectoQuerySet.as_manager()

    class Meta:
        verbose_name = _("proyecto")
        verbose_name_plural = _("proyectos")
        ordering = ["-actualizado_en"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._slug_unico()
        super().save(*args, **kwargs)

    def _slug_unico(self):
        """Convierte el título en una dirección legible y le suma un número si ya existe."""
        base = slugify(self.titulo)[:120] or "proyecto"
        slug, n = base, 2
        while Proyecto.objects.filter(slug=slug).exists():
            slug, n = f"{base}-{n}", n + 1
        return slug

    def get_absolute_url(self):
        return reverse("vitrina:detalle", args=[self.slug])

    @property
    def publicado(self):
        return self.estado == Estado.APROBADO

    @property
    def editable(self):
        return self.estado in ESTADOS_EDITABLES

    @property
    def creador(self):
        autoria = self.autorias.filter(es_creador=True).select_related("usuario").first()
        return autoria.usuario if autoria else None

    @property
    def portada(self):
        """Primera imagen de la galería (o None)."""
        imagenes = list(self.imagenes.all())
        return imagenes[0] if imagenes else None

    def es_autor(self, usuario):
        return usuario.is_authenticated and self.autorias.filter(usuario=usuario).exists()

    @property
    def ultima_decision(self):
        """El último evento con decisión de un docente (observaciones, aprobado o rechazado)."""
        return (
            self.eventos.filter(estado_nuevo__in=ESTADOS_DE_DECISION)
            .select_related("actor").order_by("-creado_en", "-id").first()
        )


class Autoria(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="autorias")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="autorias")
    es_creador = models.BooleanField(_("es el creador"), default=False)
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("autoría")
        verbose_name_plural = _("autorías")
        ordering = ["-es_creador", "agregado_en"]
        constraints = [models.UniqueConstraint(fields=["proyecto", "usuario"], name="autor_unico_por_proyecto")]

    def __str__(self):
        return f"{self.usuario} · {self.proyecto}"


class Imagen(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="imagenes")
    archivo = models.ImageField(_("imagen"), upload_to=ruta_imagen, validators=[validar_imagen])
    orden = models.PositiveSmallIntegerField(_("orden"), default=0)

    class Meta:
        verbose_name = _("imagen")
        verbose_name_plural = _("imágenes")
        ordering = ["orden", "id"]

    def __str__(self):
        return f"{self.proyecto} · {self.orden}"


# --------------------------------------------------------------------------- Historial


class HistorialInmutable(Exception):
    """Se lanza si alguien intenta editar o borrar un evento del historial."""


class EventoEstado(models.Model):
    """Un cambio de estado de un proyecto (constitución, principio VII).

    Se crea solo desde servicios.cambiar_estado. Una vez guardado no se puede modificar ni
    borrar: save() rechaza cambios y delete() está bloqueado. PROTECT impide además borrar el
    proyecto o el usuario mientras tengan historial.
    """

    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name="eventos", verbose_name=_("proyecto"))
    estado_anterior = models.CharField(_("estado anterior"), max_length=20, choices=Estado.choices)
    estado_nuevo = models.CharField(_("estado nuevo"), max_length=20, choices=Estado.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="eventos_estado", verbose_name=_("hecho por"),
    )
    comentario = models.TextField(_("comentario"), blank=True)
    creado_en = models.DateTimeField(_("fecha"), auto_now_add=True)

    class Meta:
        verbose_name = _("evento del historial")
        verbose_name_plural = _("historial de estados")
        ordering = ["creado_en", "id"]

    def __str__(self):
        return f"{self.proyecto} · {self.get_estado_anterior_display()} → {self.get_estado_nuevo_display()}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise HistorialInmutable("Los eventos del historial no se pueden modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise HistorialInmutable("Los eventos del historial no se pueden borrar.")


class Consecutivo(models.Model):
    """Último número usado por año para los códigos VP-AAAA-NNNN."""

    anio = models.PositiveSmallIntegerField(_("año"), primary_key=True)
    ultimo = models.PositiveIntegerField(_("último número"), default=0)

    class Meta:
        verbose_name = _("consecutivo de códigos")
        verbose_name_plural = _("consecutivos de códigos")

    def __str__(self):
        return f"{self.anio}: {self.ultimo}"

