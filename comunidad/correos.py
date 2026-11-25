"""Correo que avisa a quien comentó que un autor le respondió (spec 008, opcional)."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import translation

logger = logging.getLogger(__name__)


def avisar_respuesta(request, comentario, respuesta):
    """Envía el aviso. Si el correo falla, la respuesta ya está guardada: solo se registra el error."""
    destinatario = comentario.autor
    if not destinatario.is_active:
        return
    proyecto = comentario.proyecto
    with translation.override(settings.LANGUAGE_CODE):
        contexto = {
            "comentario": comentario, "respuesta": respuesta, "proyecto": proyecto,
            "enlace": request.build_absolute_uri(f"{proyecto.get_absolute_url()}#comentario-{respuesta.pk}"),
        }
        asunto = "".join(render_to_string("comunidad/correos/respuesta_asunto.txt", contexto).splitlines())
        texto = render_to_string("comunidad/correos/respuesta.txt", contexto)
    try:
        EmailMessage(subject=asunto, body=texto, to=[destinatario.email]).send()
    except Exception:
        logger.exception("No se pudo avisar la respuesta al comentario %s", comentario.pk)
