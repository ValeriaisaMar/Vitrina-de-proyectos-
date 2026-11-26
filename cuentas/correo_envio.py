"""Probar y guardar la cuenta de correo de envío (spec 008, historia 3)."""

import smtplib
import socket
import ssl

from django.core.mail import EmailMessage
from django.utils import timezone
from django.utils.translation import gettext as _

from config.correo import backend_smtp
from cuentas.cifrado import cifrar
from cuentas.models import ConfiguracionCorreo

# Configuración rápida: (servidor, puerto, seguridad)
PROVEEDORES = {
    "gmail": ("smtp.gmail.com", 587, "starttls"),
    "outlook": ("smtp.office365.com", 587, "starttls"),
}


# Códigos con los que Microsoft 365 responde cuando la cuenta tiene apagada la autenticación básica
# (SMTP AUTH): 5.7.139 "basic authentication is disabled" y 5.7.30 (spec 009).
CODIGOS_MICROSOFT_SIN_SMTP_AUTH = ("5.7.139", "5.7.30")


def proveedor_de(form, pedido=None):
    """gmail, outlook o personalizado: el pedido con ?proveedor= o, si no, el del servidor escrito."""
    if pedido in ("gmail", "outlook", "personalizado"):
        return pedido
    servidor = str(form["servidor"].value() or "").strip().lower()
    for nombre, (host, _puerto, _seguridad) in PROVEEDORES.items():
        if servidor == host:
            return nombre
    return "personalizado" if servidor else "gmail"


def _es_bloqueo_de_microsoft(error):
    """True si el servidor respondió con un código de autenticación básica desactivada."""
    detalle = getattr(error, "smtp_error", b"")
    if isinstance(detalle, bytes):
        detalle = detalle.decode("utf-8", "replace")
    return any(codigo in str(detalle) for codigo in CODIGOS_MICROSOFT_SIN_SMTP_AUTH)


def mensaje_de_error(error):
    """Traduce una excepción de SMTP a un mensaje que el admin entienda. Nunca incluye la contraseña."""
    if isinstance(error, smtplib.SMTPResponseException) and _es_bloqueo_de_microsoft(error):
        return _("Microsoft bloqueó el inicio de sesión con contraseña para esta cuenta. Usa una cuenta institucional con SMTP AUTH habilitado o una cuenta de Gmail.")
    if isinstance(error, smtplib.SMTPAuthenticationError):
        return _("El servidor rechazó el usuario o la contraseña. En Gmail usa una contraseña de aplicación, no la contraseña normal de la cuenta.")
    if isinstance(error, ssl.SSLError):
        return _("Hubo un problema con la conexión segura (TLS/SSL). Revisa que la seguridad y el puerto coincidan: STARTTLS suele ir con 587 y SSL/TLS con 465.")
    if isinstance(error, (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, socket.timeout, TimeoutError,
                          ConnectionError, socket.gaierror)):
        return _("El servidor o el puerto no responden. Revisa que estén bien escritos y que la red permita la conexión.")
    if isinstance(error, smtplib.SMTPRecipientsRefused):
        return _("El servidor no aceptó el correo de destino de la prueba.")
    if isinstance(error, smtplib.SMTPSenderRefused):
        return _("El servidor no aceptó el correo del remitente. Muchos servidores solo dejan enviar desde la misma cuenta con la que inicias sesión.")
    if isinstance(error, smtplib.SMTPException):
        return _("El servidor de correo respondió con un error. Revisa los datos e intenta de nuevo.")
    if isinstance(error, OSError):
        return _("El servidor o el puerto no responden. Revisa que estén bien escritos y que la red permita la conexión.")
    return _("No se pudo enviar el correo de prueba.")


def probar(datos, destinatario):
    """Se conecta con los datos del formulario (sin guardarlos), inicia sesión y envía un correo de prueba.

    datos: dict con servidor, puerto, seguridad, usuario, clave, nombre_remitente y correo_remitente.
    Devuelve (True, mensaje) si se envió o (False, mensaje de error comprensible).
    """
    from email.utils import formataddr

    remitente = formataddr((datos["nombre_remitente"], datos["correo_remitente"] or datos["usuario"]))
    backend = backend_smtp(datos["servidor"], datos["puerto"], datos["seguridad"], datos["usuario"], datos["clave"], timeout=15)
    mensaje = EmailMessage(
        subject=_("Prueba de correo de la Vitrina de Proyectos"),
        body=_("Si recibes este mensaje, la configuración de correo de la Vitrina de Proyectos funciona."),
        from_email=remitente,
        to=[destinatario],
    )
    try:
        backend.send_messages([mensaje])
    except Exception as error:  # se traduce a un mensaje claro; nunca se muestra el detalle técnico
        return False, mensaje_de_error(error)
    return True, _("Enviamos un correo de prueba a %(correo)s. Revisa la bandeja de entrada (y la de spam).") % {"correo": destinatario}


def guardar(datos, actor, configuracion=None):
    """Guarda la configuración. Si la contraseña llega vacía, se conserva la anterior."""
    configuracion = configuracion or ConfiguracionCorreo.actual() or ConfiguracionCorreo()
    for campo in ("servidor", "puerto", "seguridad", "usuario", "nombre_remitente", "correo_remitente"):
        setattr(configuracion, campo, datos[campo])
    if datos.get("clave"):
        configuracion.clave_cifrada = cifrar(datos["clave"])
    configuracion.actualizado_por = actor
    configuracion.save()
    return configuracion


def registrar_prueba(ok, mensaje):
    """Guarda el resultado de la última prueba en la configuración, si existe."""
    configuracion = ConfiguracionCorreo.actual()
    if configuracion is None:
        return
    ConfiguracionCorreo.objects.filter(pk=configuracion.pk).update(
        ultima_prueba_en=timezone.now(), ultima_prueba_ok=ok, ultima_prueba_mensaje=mensaje[:300],
    )
