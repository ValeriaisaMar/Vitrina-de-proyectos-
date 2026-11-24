"""Correo que avisa a los autores de la decisión del docente."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

logger = logging.getLogger(__name__)


def avisar_decision(request, proyecto, evento):
    """Envía a todos los autores un correo con la decisión. Devuelve True si se envió.

    Se llama cuando la decisión ya está guardada: si el correo falla, la decisión no se pierde;
    se registra el error y la vista avisa al docente.
    Los correos van en el idioma por defecto (español), aunque el docente navegue en inglés.
    """
    destinatarios = list(proyecto.autores.filter(is_active=True).values_list("email", flat=True))
    if not destinatarios:
        return True
    contexto = {
        "proyecto": proyecto,
        "evento": evento,
        "enlace": request.build_absolute_uri(proyecto.get_absolute_url()),
    }
    with translation.override(settings.LANGUAGE_CODE):
        asunto = "".join(render_to_string("proyectos/correos/decision_asunto.txt", contexto).splitlines())
        texto = render_to_string("proyectos/correos/decision.txt", contexto)
        html = render_to_string("proyectos/correos/decision.html", contexto)
    mensaje = EmailMultiAlternatives(subject=asunto, body=texto, to=destinatarios)
    mensaje.attach_alternative(html, "text/html")
    try:
        mensaje.send()
    except Exception:
        logger.exception("No se pudo enviar el aviso de decisión del proyecto %s", proyecto.pk)
        return False
    return True
