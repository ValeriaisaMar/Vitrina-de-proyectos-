"""Modelos de la app proyectos.

- PlanEstudio y Asignatura: planes de estudio y sus asignaturas, que el admin administra en la app.
- Tecnologia: catálogo de tecnologías.
- Periodo: periodos académicos (ordinarios, intersemestrales, intensivos…) que crea el admin.
- Proyecto: el trabajo de uno o varios estudiantes.
- Autoria: une a cada autor con su proyecto y marca al creador.
- Imagen: capturas de la galería del proyecto.
- EventoEstado: historial de cambios de estado; nunca se edita ni se borra.
- Consecutivo: contador por año para los códigos VP-AAAA-NNNN.

Los campos estado, revisor, periodo, codigo, aprobado_en y periodo_aprobacion solo los cambia
proyectos/servicios.py (el período, al enviar y al aprobar).
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from proyectos.paleta import COLOR_POR_DEFECTO, OPCIONES_COLOR, hex_de
from proyectos.validadores import validar_imagen, validar_pdf, validar_url_web

MAX_AUTORES = 6
MAX_IMAGENES = 4
MAX_TECNOLOGIAS = 8


# --------------------------------------------------------------------------- Catálogos


class PlanEstudio(models.Model):
    """Plan de estudios de la carrera, por ejemplo "Plan 2022" (spec 009, historia 3).

    Puede haber más de uno activo a la vez (transición entre planes). Un plan con asignaturas no
    se borra: se desactiva, y sus asignaturas dejan de ofrecerse en los formularios.
    """

    nombre = models.CharField(_("nombre"), max_length=80, unique=True)
    anio = models.PositiveSmallIntegerField(_("año"), validators=[MinValueValidator(1990), MaxValueValidator(2100)])
    activo = models.BooleanField(_("activo"), default=True)

    class Meta:
        verbose_name = _("plan de estudios")
        verbose_name_plural = _("planes de estudio")
        ordering = ["-anio", "nombre"]

    def __str__(self):
        return self.nombre


class AsignaturaQuerySet(models.QuerySet):
    def ofrecidas(self):
        """Las que se pueden elegir en un formulario: activas y de un plan activo."""
        return self.filter(activa=True, plan__activo=True)


class Asignatura(models.Model):
    """Asignatura de un plan de estudios de Ingeniería de Software.

    El nombre se repite entre planes ("Bases de datos" en el plan 2022 y en el 2026), pero no
    dentro del mismo plan. Una asignatura en uso no se borra: se desactiva.
    """

    plan = models.ForeignKey(PlanEstudio, verbose_name=_("plan de estudios"), on_delete=models.PROTECT, related_name="asignaturas")
    nombre = models.CharField(_("nombre"), max_length=120)
    codigo = models.CharField(_("código"), max_length=20, blank=True)
    semestre = models.PositiveSmallIntegerField(
        _("semestre"), validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    activa = models.BooleanField(_("activa"), default=True)

    objects = AsignaturaQuerySet.as_manager()

    class Meta:
        verbose_name = _("asignatura")
        verbose_name_plural = _("asignaturas")
        ordering = ["semestre", "nombre"]
        constraints = [models.UniqueConstraint(fields=["plan", "nombre"], name="asignatura_unica_por_plan")]

    def __str__(self):
        return self.nombre

    @property
    def en_uso(self):
        """True si algún proyecto o profesor la usa (entonces no se puede borrar)."""
        return self.proyectos.exists() or (hasattr(self, "profesores") and self.profesores.exists())


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


CLAVE_CACHE_PERIODO = "periodo_actual"
_SIN_PERIODO = "sin-periodo"  # en la caché, "no hay período actual" (None no se distingue de "no está")


class Periodo(models.Model):
    """Periodo académico (spec 008). Lo crea el admin desde la app.

    El nombre es libre ("2026-2", "Intensivo noviembre 2026"); la fecha de inicio sirve para
    ordenar del más reciente al más antiguo. Un periodo con proyectos no se borra.

    Spec 009: solo uno es el "período actual" (es_actual): el único en el que se pueden enviar
    proyectos. Lo garantiza la base de datos con una restricción única condicional.
    """

    nombre = models.CharField(_("nombre"), max_length=60, unique=True)
    slug = models.SlugField(_("dirección"), max_length=70, unique=True, editable=False)
    tipo = models.CharField(_("tipo"), max_length=15, choices=TipoPeriodo.choices, default=TipoPeriodo.ORDINARIO)
    fecha_inicio = models.DateField(_("fecha de inicio"))
    fecha_fin = models.DateField(_("fecha de fin"), null=True, blank=True)
    es_actual = models.BooleanField(
        _("período actual"), default=False,
        help_text=_("El único período en el que los estudiantes pueden enviar proyectos."),
    )

    class Meta:
        verbose_name = _("periodo académico")
        verbose_name_plural = _("periodos académicos")
        ordering = ["-fecha_inicio", "-id"]
        constraints = [
            # Como mucho una fila con es_actual=True; las demás (False) no cuentan
            models.UniqueConstraint(fields=["es_actual"], condition=models.Q(es_actual=True), name="un_solo_periodo_actual"),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._slug_unico()
        super().save(*args, **kwargs)
        cache.delete(CLAVE_CACHE_PERIODO)

    def delete(self, *args, **kwargs):
        resultado = super().delete(*args, **kwargs)
        cache.delete(CLAVE_CACHE_PERIODO)
        return resultado

    @classmethod
    def actual(cls):
        """El período actual, o None si el admin no ha marcado ninguno. Se guarda en caché.

        Lo leen el pie de página y el menú en cada petición: sin caché sería una consulta por página.
        save() y delete() borran la caché, así un cambio se ve de inmediato.
        """
        guardado = cache.get(CLAVE_CACHE_PERIODO)
        if guardado is None:
            periodo = cls.objects.filter(es_actual=True).first()
            cache.set(CLAVE_CACHE_PERIODO, periodo or _SIN_PERIODO, 60 * 60)
            return periodo
        return None if guardado == _SIN_PERIODO else guardado

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


class Subestado(models.TextChoices):
    """En qué punto está un proyecto Enviado (spec 009). No son estados nuevos: se deducen.

    - por_asignar: nadie lo tiene; el creador debe elegir un profesor.
    - esperando:   hay una solicitud pendiente; el profesor elegido todavía no responde.
    - por_revisar: ya tiene profesor asignado (reenvío tras observaciones o reasignación del admin).
    """

    POR_ASIGNAR = "por_asignar", _("Por asignar revisor")
    ESPERANDO = "esperando", _("Esperando aceptación")
    POR_REVISAR = "por_revisar", _("Por revisar")


ESTADOS_EDITABLES = {Estado.BORRADOR, Estado.CON_OBSERVACIONES}
ESTADOS_DE_DECISION = {Estado.APROBADO, Estado.CON_OBSERVACIONES, Estado.RECHAZADO}


def ruta_documento(instancia, nombre_original):
    """Guarda el PDF con un nombre aleatorio para no exponer ni pisar nombres de archivo."""
    return f"proyectos/documentos/{uuid.uuid4().hex}.pdf"


def ruta_portada(instancia, nombre):
    """La portada ya llega convertida a webp con un nombre aleatorio (config/imagenes.py)."""
    return f"proyectos/portadas/{nombre}"


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
        return self.select_related("asignatura", "periodo", "periodo_aprobacion").prefetch_related("tecnologias", "autores", "imagenes")

    def con_subestado(self):
        """Anota si hay una solicitud pendiente: Proyecto.subestado no hace consultas extra en listas."""
        pendiente = SolicitudRevision.objects.filter(proyecto=models.OuterRef("pk"), estado=EstadoSolicitud.PENDIENTE)
        return self.annotate(tiene_solicitud_pendiente=models.Exists(pendiente))


class Proyecto(models.Model):
    titulo = models.CharField(_("título"), max_length=120)
    slug = models.SlugField(_("dirección"), max_length=140, unique=True, editable=False)
    resumen = models.CharField(_("resumen"), max_length=300, help_text=_("Una o dos frases. Aparece en las tarjetas."))
    descripcion = models.TextField(_("descripción"))
    asignatura = models.ForeignKey(Asignatura, verbose_name=_("asignatura"), on_delete=models.PROTECT, related_name="proyectos")
    # Spec 009: el borrador no tiene período; lo toma al enviarse (el período actual de ese momento)
    periodo = models.ForeignKey(
        Periodo, verbose_name=_("periodo"), on_delete=models.PROTECT, related_name="proyectos", null=True, blank=True,
    )
    tecnologias = models.ManyToManyField(Tecnologia, verbose_name=_("tecnologías"), related_name="proyectos")
    repositorio = models.URLField(_("repositorio"), validators=[validar_url_web])
    demo = models.URLField(_("proyecto desplegado"), blank=True, validators=[validar_url_web])
    # Spec 009, historia 7: enlace al video (solo se enlaza, no se incrusta) y la cara del proyecto
    video = models.URLField(_("video"), blank=True, validators=[validar_url_web])
    imagen_portada = models.ImageField(_("imagen de portada"), upload_to=ruta_portada, blank=True)
    color_portada = models.CharField(_("color de la portada"), max_length=12, choices=OPCIONES_COLOR, default=COLOR_POR_DEFECTO)
    documento_pdf = models.FileField(_("documento PDF"), upload_to=ruta_documento, blank=True, validators=[validar_pdf])

    autores = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Autoria", related_name="proyectos", verbose_name=_("autores"))
    estado = models.CharField(_("estado"), max_length=20, choices=Estado.choices, default=Estado.BORRADOR, db_index=True)

    # El profesor asignado (spec 009): lo fijan proyectos/solicitudes.py al aceptar una solicitud o
    # cuando el admin reasigna. codigo y aprobado_en los llena servicios.cambiar_estado al aprobar.
    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("revisor"), on_delete=models.SET_NULL,
        null=True, blank=True, related_name="proyectos_revisados",
    )
    codigo = models.CharField(_("código de verificación"), max_length=12, unique=True, null=True, blank=True)
    aprobado_en = models.DateTimeField(_("aprobado en"), null=True, blank=True)
    # Período en que se aprobó: puede ser distinto del de envío si la revisión cruzó de período
    periodo_aprobacion = models.ForeignKey(
        Periodo, verbose_name=_("periodo de aprobación"), on_delete=models.PROTECT,
        related_name="proyectos_aprobados", null=True, blank=True,
    )

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
    def color_hex(self):
        """Código del color de la portada (spec 009)."""
        return hex_de(self.color_portada)

    @property
    def url_imagen_compartir(self):
        """La imagen para la vista previa al compartir: la portada o, si no hay, la primera de la galería."""
        if self.imagen_portada:
            return self.imagen_portada.url
        primera = self.portada
        return primera.archivo.url if primera else None

    @property
    def portada(self):
        """Primera imagen de la galería (o None). La cara del proyecto es imagen_portada (spec 009)."""
        imagenes = list(self.imagenes.all())
        return imagenes[0] if imagenes else None

    def es_autor(self, usuario):
        return usuario.is_authenticated and self.autorias.filter(usuario=usuario).exists()

    @property
    def subestado(self):
        """Subestado de un proyecto Enviado (ver Subestado), o None si está en otro estado."""
        if self.estado != Estado.ENVIADO:
            return None
        if self.revisor_id:
            return Subestado.POR_REVISAR
        pendiente = getattr(self, "tiene_solicitud_pendiente", None)
        if pendiente is None:
            pendiente = self.solicitudes.filter(estado=EstadoSolicitud.PENDIENTE).exists()
        return Subestado.ESPERANDO if pendiente else Subestado.POR_ASIGNAR

    def get_subestado_display(self):
        return Subestado(self.subestado).label if self.subestado else ""

    @property
    def solicitud_pendiente(self):
        """La solicitud de revisión que espera respuesta, o None."""
        return self.solicitudes.filter(estado=EstadoSolicitud.PENDIENTE).select_related("profesor").first()

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


class AccionEvento(models.TextChoices):
    """Qué registra un evento del historial (spec 009)."""

    ESTADO = "estado", _("Cambio de estado")
    SOLICITUD = "solicitud", _("Solicitud de revisión")
    ACEPTADA = "aceptada", _("Aceptó revisar")
    NO_ACEPTADA = "no_aceptada", _("No aceptó revisar")
    RETIRADA = "retirada", _("Solicitud retirada")
    REASIGNADA = "reasignada", _("Revisor reasignado")


class EventoEstado(models.Model):
    """Un cambio de estado de un proyecto (constitución, principio VII).

    Se crea solo desde servicios.cambiar_estado. Una vez guardado no se puede modificar ni
    borrar: save() rechaza cambios y delete() está bloqueado. PROTECT impide además borrar el
    proyecto o el usuario mientras tengan historial.
    """

    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name="eventos", verbose_name=_("proyecto"))
    # Spec 009: además de los cambios de estado, el historial guarda el flujo de las solicitudes de
    # revisión. En esos eventos el estado puede no cambiar (anterior == nuevo).
    accion = models.CharField(_("acción"), max_length=15, choices=AccionEvento.choices, default=AccionEvento.ESTADO)
    # El profesor al que se refiere la acción: a quién se le pidió, a quién se reasignó o a quién recomendó
    profesor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("profesor"),
    )
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


class EstadoSolicitud(models.TextChoices):
    PENDIENTE = "pendiente", _("Pendiente")
    ACEPTADA = "aceptada", _("Aceptada")
    NO_ACEPTADA = "no_aceptada", _("No aceptada")
    RETIRADA = "retirada", _("Retirada")
    REASIGNADA = "reasignada", _("Reasignada")


DIAS_PARA_RETIRAR = 5  # si el profesor no responde en estos días, el creador puede retirar la solicitud


class SolicitudRevision(models.Model):
    """Pedido del creador a un profesor para que revise su proyecto (spec 009, historia 5).

    Un proyecto tiene como mucho una solicitud pendiente (restricción de la base de datos). Las
    demás quedan como registro: aceptada, no aceptada (con mensaje y recomendación opcionales),
    retirada por el creador o reasignada por el admin. Solo las cambia proyectos/solicitudes.py.
    """

    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name="solicitudes", verbose_name=_("proyecto"))
    profesor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes_revision", verbose_name=_("profesor"),
    )
    estado = models.CharField(_("estado"), max_length=12, choices=EstadoSolicitud.choices, default=EstadoSolicitud.PENDIENTE, db_index=True)
    mensaje = models.TextField(_("mensaje"), blank=True, max_length=1000)
    profesor_recomendado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name=_("profesor recomendado"),
    )
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name=_("creada por"),
    )
    creada_en = models.DateTimeField(_("creada en"), auto_now_add=True)
    respondida_en = models.DateTimeField(_("respondida en"), null=True, blank=True)
    recordatorio_enviado = models.BooleanField(_("recordatorio enviado"), default=False)

    class Meta:
        verbose_name = _("solicitud de revisión")
        verbose_name_plural = _("solicitudes de revisión")
        ordering = ["-creada_en", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["proyecto"], condition=models.Q(estado="pendiente"), name="una_solicitud_pendiente_por_proyecto",
            ),
        ]

    def __str__(self):
        return f"{self.proyecto} → {self.profesor} ({self.get_estado_display()})"

    @property
    def se_puede_retirar_desde(self):
        from datetime import timedelta

        return self.creada_en + timedelta(days=DIAS_PARA_RETIRAR)


class Consecutivo(models.Model):
    """Último número usado por año para los códigos VP-AAAA-NNNN."""

    anio = models.PositiveSmallIntegerField(_("año"), primary_key=True)
    ultimo = models.PositiveIntegerField(_("último número"), default=0)

    class Meta:
        verbose_name = _("consecutivo de códigos")
        verbose_name_plural = _("consecutivos de códigos")

    def __str__(self):
        return f"{self.anio}: {self.ultimo}"

