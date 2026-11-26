"""Correos de proyectos: la decisión del docente, transferencias, salidas y solicitudes de revisión."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from config.correo import CorreoConLogo

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
    mensaje = CorreoConLogo(subject=asunto, body=texto, to=destinatarios)
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


# --------------------------------------------------------------------------- Solicitudes de revisión (spec 009)


def base_url(request):
    """Dirección base del sitio para los enlaces de los correos (SITIO_URL o la de la petición)."""
    return settings.SITIO_URL or request.build_absolute_uri("/").rstrip("/")


def _avisar(plantilla, asunto, contexto, destinatarios, que):
    """Envía un correo de texto en español. Si falla, la acción ya está guardada: solo se registra."""
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return True
    with translation.override(settings.LANGUAGE_CODE):
        cuerpo = render_to_string(f"proyectos/correos/{plantilla}.txt", contexto)
        asunto = str(asunto(contexto))
    try:
        EmailMessage(subject=asunto, body=cuerpo, to=destinatarios).send()
    except Exception:
        logger.exception("No se pudo enviar el aviso de %s", que)
        return False
    return True


def _autores(proyecto):
    return list(proyecto.autores.filter(is_active=True).values_list("email", flat=True))


def avisar_solicitud(base, solicitud, recordatorio=False):
    """Al profesor: un estudiante le pide revisar su proyecto (o el recordatorio del tercer día)."""
    proyecto = solicitud.proyecto
    contexto = {"solicitud": solicitud, "proyecto": proyecto, "recordatorio": recordatorio,
                "enlace": base + reverse("proyectos:solicitudes")}
    asunto = (lambda c: _("Recordatorio: solicitud de revisión de «%(titulo)s»") % {"titulo": proyecto.titulo}) if recordatorio \
        else (lambda c: _("Te piden revisar «%(titulo)s»") % {"titulo": proyecto.titulo})
    return _avisar("solicitud", asunto, contexto, [solicitud.profesor.email], f"la solicitud {solicitud.pk}")


def avisar_aceptada(base, proyecto, profesor):
    """A los autores: el profesor aceptó revisar el proyecto."""
    contexto = {"proyecto": proyecto, "profesor": profesor, "enlace": base + proyecto.get_absolute_url()}
    return _avisar("solicitud_aceptada", lambda c: _("%(profesor)s revisará «%(titulo)s»") % {"profesor": profesor.nombre_completo, "titulo": proyecto.titulo},
                   contexto, _autores(proyecto), f"aceptación del proyecto {proyecto.pk}")


def avisar_no_aceptada(base, solicitud):
    """A todos los autores: el profesor no aceptó, con su mensaje y su recomendación."""
    proyecto = solicitud.proyecto
    contexto = {"solicitud": solicitud, "proyecto": proyecto, "enlace": base + reverse("proyectos:elegir_revisor", args=[proyecto.slug])}
    return _avisar("solicitud_no_aceptada", lambda c: _("Elige otro revisor para «%(titulo)s»") % {"titulo": proyecto.titulo},
                   contexto, _autores(proyecto), f"no aceptación de la solicitud {solicitud.pk}")


def avisar_retirada(base, solicitud):
    """Al profesor: el creador retiró la solicitud que no había respondido."""
    proyecto = solicitud.proyecto
    contexto = {"solicitud": solicitud, "proyecto": proyecto}
    return _avisar("solicitud_retirada", lambda c: _("Se retiró la solicitud de revisión de «%(titulo)s»") % {"titulo": proyecto.titulo},
                   contexto, [solicitud.profesor.email], f"retiro de la solicitud {solicitud.pk}")


def avisar_reasignada(base, proyecto, profesor):
    """Al nuevo profesor: la administración le asignó la revisión del proyecto."""
    contexto = {"proyecto": proyecto, "profesor": profesor, "enlace": base + reverse("proyectos:bandeja")}
    return _avisar("revisor_asignado", lambda c: _("Te asignaron la revisión de «%(titulo)s»") % {"titulo": proyecto.titulo},
                   contexto, [profesor.email], f"reasignación del proyecto {proyecto.pk}")
