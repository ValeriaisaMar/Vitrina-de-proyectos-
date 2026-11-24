"""Envío de correos de la app cuentas."""

import logging

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from cuentas.tokens import token_activacion

logger = logging.getLogger(__name__)


def enlace_activacion(request, usuario):
    """Arma la dirección completa del enlace de activación de un usuario.

    El enlace lleva el id del usuario codificado en base64 (uid) y un token firmado que vence
    en 24 horas y deja de servir cuando la cuenta se activa.
    """
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = token_activacion.make_token(usuario)
    return request.build_absolute_uri(reverse("cuentas:activar", args=[uid, token]))


def enviar_activacion(request, usuario):
    """Envía el correo de activación en texto y HTML. Devuelve True si se envió.

    Si el servidor de correo falla, no se pierde la cuenta: se registra el error y la vista
    avisa a la persona que puede pedir el reenvío.
    """
    contexto = {"usuario": usuario, "enlace": enlace_activacion(request, usuario), "horas": 24}
    asunto = "".join(render_to_string("cuentas/correos/activacion_asunto.txt", contexto).splitlines())
    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=render_to_string("cuentas/correos/activacion.txt", contexto),
        to=[usuario.email],
    )
    mensaje.attach_alternative(render_to_string("cuentas/correos/activacion.html", contexto), "text/html")
    try:
        mensaje.send()
    except Exception:
        logger.exception("No se pudo enviar el correo de activación al usuario %s", usuario.pk)
        return False
    return True
