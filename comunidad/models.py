"""Modelos de la app comunidad (módulo 007): me gusta, guardados y comentarios.

Solo existen sobre proyectos aprobados. Me gusta y guardado son únicos por persona y proyecto:
lo garantiza la base de datos con UniqueConstraint, no solo el código.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from proyectos.models import Proyecto

MAX_COMENTARIO = 1000


class MeGusta(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="me_gustas")
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="me_gustas")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("me gusta")
        verbose_name_plural = _("me gusta")
        constraints = [models.UniqueConstraint(fields=["usuario", "proyecto"], name="un_me_gusta_por_persona")]


class Guardado(models.Model):
    """Un proyecto que una persona guardó para verlo después (antes se llamaba Favorito, spec 009).

    Hay una sola lista: "Guardados". RenameModel renombró la tabla sin tocar las filas; la
    restricción única conserva su nombre de antes.
    """

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guardados")
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="guardados")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("guardado")
        verbose_name_plural = _("guardados")
        ordering = ["-creado_en"]
        constraints = [models.UniqueConstraint(fields=["usuario", "proyecto"], name="un_favorito_por_persona")]


class ComentarioQuerySet(models.QuerySet):
    def visibles(self):
        return self.filter(oculto=False)

    def principales(self):
        """Los comentarios que no son respuesta de otro."""
        return self.filter(respuesta_a__isnull=True)


class Comentario(models.Model):
    """Comentario público sobre un proyecto. Moderar es ocultar (reversible), no borrar.

    Los autores del proyecto pueden responder (spec 008). Hay un solo nivel: una respuesta no
    se responde. Si se oculta un comentario, sus respuestas dejan de mostrarse al público.
    """

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="comentarios", verbose_name=_("proyecto"))
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios", verbose_name=_("autor"))
    texto = models.TextField(_("comentario"), max_length=MAX_COMENTARIO)
    creado_en = models.DateTimeField(_("fecha"), auto_now_add=True)

    oculto = models.BooleanField(_("oculto"), default=False)
    ocultado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="comentarios_ocultados", verbose_name=_("ocultado por"),
    )
    ocultado_en = models.DateTimeField(_("ocultado en"), null=True, blank=True)
    respuesta_a = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="respuestas", verbose_name=_("en respuesta a"),
    )

    objects = ComentarioQuerySet.as_manager()

    class Meta:
        verbose_name = _("comentario")
        verbose_name_plural = _("comentarios")
        ordering = ["creado_en", "id"]

    def __str__(self):
        return f"{self.autor} · {self.proyecto}"

    def clean(self):
        """Un solo nivel de respuesta, y del mismo proyecto."""
        from django.core.exceptions import ValidationError

        padre = self.respuesta_a
        if padre is not None:
            if padre.respuesta_a_id is not None:
                raise ValidationError(_("No se puede responder a una respuesta."), code="segundo_nivel")
            if padre.proyecto_id != self.proyecto_id:
                raise ValidationError(_("La respuesta debe ser del mismo proyecto."), code="otro_proyecto")
