"""Correo que avisa a los autores de la decisión del docente."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

from config.correo import url_logo_correo

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
        "logo_correo_url": url_logo_correo(request),
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


def avisar_transferencia(request, proyecto, anterior, nuevo):
    """Avisa al nuevo creador que ahora el proyecto está a su cargo."""
    with translation.override(settings.LANGUAGE_CODE):
        contexto = {
            "proyecto": proyecto, "anterior": anterior, "nuevo": nuevo,
            "enlace": request.build_absolute_uri(proyecto.get_absolute_url()),
        }
        asunto = "".join(render_to_string("proyectos/correos/transferencia_asunto.txt", contexto).splitlines())
        texto = render_to_string("proyectos/correos/transferencia.txt", contexto)
    try:
        EmailMessage(subject=asunto, body=texto, to=[nuevo.email]).send()
    except Exception:
        logger.exception("No se pudo avisar la transferencia del proyecto %s", proyecto.pk)


def avisar_salida(request, proyecto, coautor):
    """Avisa al creador que un coautor dejó el proyecto. Si el correo falla, solo se registra."""
    creador = proyecto.creador
    if creador is None or not creador.is_active:
        return
    with translation.override(settings.LANGUAGE_CODE):
        contexto = {
            "proyecto": proyecto, "coautor": coautor, "creador": creador,
            "enlace": request.build_absolute_uri(proyecto.get_absolute_url()),
        }
        asunto = "".join(render_to_string("proyectos/correos/salida_asunto.txt", contexto).splitlines())
        texto = render_to_string("proyectos/correos/salida.txt", contexto)
    try:
        EmailMessage(subject=asunto, body=texto, to=[creador.email]).send()
    except Exception:
        logger.exception("No se pudo avisar la salida del coautor %s del proyecto %s", coautor.pk, proyecto.pk)
