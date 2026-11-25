"""Modelos de la app comunidad (módulo 007): me gusta, favoritos y comentarios.

Solo existen sobre proyectos aprobados. Me gusta y favorito son únicos por persona y proyecto:
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


class Favorito(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favoritos")
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="favoritos")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("favorito")
        verbose_name_plural = _("favoritos")
        ordering = ["-creado_en"]
        constraints = [models.UniqueConstraint(fields=["usuario", "proyecto"], name="un_favorito_por_persona")]


class ComentarioQuerySet(models.QuerySet):
    def visibles(self):
        return self.filter(oculto=False)


class Comentario(models.Model):
    """Comentario público sobre un proyecto. Moderar es ocultar (reversible), no borrar."""

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

    objects = ComentarioQuerySet.as_manager()

    class Meta:
        verbose_name = _("comentario")
        verbose_name_plural = _("comentarios")
        ordering = ["creado_en", "id"]

    def __str__(self):
        return f"{self.autor} · {self.proyecto}"
