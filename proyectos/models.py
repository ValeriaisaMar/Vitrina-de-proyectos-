"""Modelos de la app proyectos.

- Asignatura y Tecnologia: catálogos que administra el admin.
- Proyecto: el trabajo de uno o varios estudiantes.
- Autoria: une a cada autor con su proyecto y marca al creador.
- Imagen: capturas de la galería del proyecto.

Los campos codigo, revisor y aprobado_en se llenan en los módulos 004 y 005.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from proyectos.validadores import validar_imagen, validar_pdf, validar_periodo, validar_url_web

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


# --------------------------------------------------------------------------- Proyecto


class Estado(models.TextChoices):
    """Estados del proyecto (constitución, principio VII). Los cambios llegan en el módulo 004."""

    BORRADOR = "borrador", _("Borrador")
    ENVIADO = "enviado", _("Enviado")
    EN_REVISION = "en_revision", _("En revisión")
    CON_OBSERVACIONES = "con_observaciones", _("Con observaciones")
    APROBADO = "aprobado", _("Aprobado")
    RECHAZADO = "rechazado", _("Rechazado")


ESTADOS_EDITABLES = {Estado.BORRADOR, Estado.CON_OBSERVACIONES}


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
        return self.select_related("asignatura").prefetch_related("tecnologias", "autores", "imagenes")


class Proyecto(models.Model):
    titulo = models.CharField(_("título"), max_length=120)
    slug = models.SlugField(_("dirección"), max_length=140, unique=True, editable=False)
    resumen = models.CharField(_("resumen"), max_length=300, help_text=_("Una o dos frases. Aparece en las tarjetas."))
    descripcion = models.TextField(_("descripción"))
    asignatura = models.ForeignKey(Asignatura, verbose_name=_("asignatura"), on_delete=models.PROTECT, related_name="proyectos")
    periodo = models.CharField(_("periodo"), max_length=6, validators=[validar_periodo])
    tecnologias = models.ManyToManyField(Tecnologia, verbose_name=_("tecnologías"), related_name="proyectos")
    repositorio = models.URLField(_("repositorio"), validators=[validar_url_web])
    demo = models.URLField(_("demo en línea"), blank=True, validators=[validar_url_web])
    documento_pdf = models.FileField(_("documento PDF"), upload_to=ruta_documento, blank=True, validators=[validar_pdf])

    autores = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Autoria", related_name="proyectos", verbose_name=_("autores"))
    estado = models.CharField(_("estado"), max_length=20, choices=Estado.choices, default=Estado.BORRADOR, db_index=True)

    # Se llenan en los módulos 004 (revisión) y 005 (verificación)
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
