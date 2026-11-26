"""Backend de correo configurable desde la app (spec 008, historia 3).

Django 6.1 configura el correo con MAILERS en settings.py: cada entrada dice qué clase (BACKEND)
envía los mensajes y con qué opciones (OPTIONS). Aquí MAILERS["default"] apunta a
CorreoConfigurableBackend, que en cada envío decide:

- Si el admin guardó una ConfiguracionCorreo con contraseña → SMTP con esos datos y el remitente
  configurado ("Vitrina de Proyectos UTEQ <correo@...>").
- Si no → el "respaldo" que llega en OPTIONS: el SMTP de Gmail con los datos del .env, o la
  consola si el .env no tiene contraseña. Es decir, todo funciona como antes de esta historia.

La configuración se lee de la base con caché; ConfiguracionCorreo.save() borra la caché, así el
siguiente correo ya usa los datos nuevos. Los correos de cuentas/ y proyectos/ no cambian.
"""

import logging
from email.utils import formataddr

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

SEGUNDOS_CACHE = 5 * 60
CONSOLA = {"BACKEND": "django.core.mail.backends.console.EmailBackend"}


def datos_vigentes():
    """Los datos de envío guardados por el admin (dict) o None. Con caché.

    Nunca devuelve ni registra la contraseña en claro fuera de este proceso: se descifra al enviar.
    """
    from cuentas.models import CLAVE_CACHE_CORREO, ConfiguracionCorreo  # import local: las apps cargan después

    datos = cache.get(CLAVE_CACHE_CORREO)
    if datos is None:
        configuracion = ConfiguracionCorreo.actual()
        if configuracion and configuracion.tiene_clave:
            datos = {
                "servidor": configuracion.servidor,
                "puerto": configuracion.puerto,
                "seguridad": configuracion.seguridad,
                "usuario": configuracion.usuario,
                "clave_cifrada": configuracion.clave_cifrada,
                "remitente": formataddr((configuracion.nombre_remitente, configuracion.remitente)),
            }
        else:
            datos = {}  # "no hay configuración" también se guarda en caché
        cache.set(CLAVE_CACHE_CORREO, datos, SEGUNDOS_CACHE)
    return datos or None


def backend_smtp(servidor, puerto, seguridad, usuario, clave, alias=None, timeout=20):
    """Un backend SMTP de Django con estos datos. Lo usan el envío normal y el botón de prueba."""
    return SmtpBackend(
        alias=alias or "configurable", host=servidor, port=puerto, username=usuario, password=clave,
        use_tls=seguridad == "starttls", use_ssl=seguridad == "ssl", timeout=timeout,
    )


class CorreoConfigurableBackend(BaseEmailBackend):
    """Envía con la configuración de la app o, si no existe, con el respaldo del .env."""

    def __init__(self, respaldo=None, timeout=20, **kwargs):
        super().__init__(**kwargs)
        self.respaldo = respaldo or CONSOLA
        self.timeout = timeout

    def _respaldo(self):
        clase = import_string(self.respaldo["BACKEND"])
        return clase(alias=self.alias, **self.respaldo.get("OPTIONS", {}))

    def _elegir(self):
        """Devuelve (backend, remitente). remitente es None cuando se usa el respaldo."""
        datos = datos_vigentes()
        if not datos:
            return self._respaldo(), None
        from cuentas.cifrado import ClaveIlegible, descifrar

        try:
            clave = descifrar(datos["clave_cifrada"])
        except Exception as error:  # clave ilegible o CLAVE_CIFRADO ausente: mejor el respaldo que no enviar
            if not isinstance(error, ClaveIlegible):
                logger.warning("No se pudo leer la configuración de correo de la app (%s); se usa el .env.", type(error).__name__)
            else:
                logger.warning("La contraseña del correo guardada no se pudo descifrar; se usa el .env.")
            return self._respaldo(), None
        backend = backend_smtp(datos["servidor"], datos["puerto"], datos["seguridad"], datos["usuario"], clave,
                               alias=self.alias, timeout=self.timeout)
        return backend, datos["remitente"]

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        backend, remitente = self._elegir()
        if remitente:
            for mensaje in email_messages:
                # Solo se cambia el remitente por defecto; si un correo trae uno propio, se respeta
                if mensaje.from_email in (None, "", settings.DEFAULT_FROM_EMAIL):
                    mensaje.from_email = remitente
        return backend.send_messages(email_messages)


# --------------------------------------------------------------------------- Marca en los correos

LOGO_CORREO = "img/marca/uteq-correo.png"
CID_LOGO = "logo-uteq"


def incrustar_logo(mensaje_mime):
    """Mete el logo UTEQ DENTRO del correo, junto a la parte HTML (multipart/related).

    Antes el <img> apuntaba a una dirección como http://127.0.0.1:8000/static/...: Gmail y Outlook
    descargan las imágenes desde sus servidores, que no pueden entrar a tu computador, así que el
    logo salía roto. Incrustado viaja con el correo y se ve siempre, en local y en producción.
    La plantilla lo pide con src="cid:logo-uteq" (cuentas/templates/cuentas/correos/base_correo.html).
    """
    ruta = finders.find(LOGO_CORREO)
    if not ruta:
        logger.warning("No se encontró %s; el correo sale sin logo.", LOGO_CORREO)
        return mensaje_mime
    for parte in mensaje_mime.walk():
        if parte.get_content_type() == "text/html" and f"cid:{CID_LOGO}" in parte.get_content():
            with open(ruta, "rb") as archivo:
                parte.add_related(archivo.read(), "image", "png", cid=f"<{CID_LOGO}>",
                                  disposition="inline", filename="uteq.png")
            break
    return mensaje_mime


class CorreoConLogo(EmailMultiAlternatives):
    """EmailMultiAlternatives que incrusta el logo UTEQ en la versión HTML. Úsenlo para todo correo HTML."""

    def message(self, **kwargs):
        return incrustar_logo(super().message(**kwargs))
