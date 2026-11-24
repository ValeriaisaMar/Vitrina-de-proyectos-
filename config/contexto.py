"""Procesadores de contexto: datos que todas las plantillas reciben automáticamente."""

from django.contrib.staticfiles import finders
from django.templatetags.static import static

# Nombres de archivo que se buscan en static/img/, en este orden.
_LOGOS_POSIBLES = ("img/logo-uteq.svg", "img/logo-uteq.png", "img/logo-uteq.webp")


def _buscar_logo():
    for ruta in _LOGOS_POSIBLES:
        if finders.find(ruta):
            return static(ruta)
    return None


def marca(request):
    """Entrega la URL del logo si el equipo ya lo copió en static/img/; si no, None.

    Las plantillas muestran el nombre de la plataforma en texto cuando no hay logo, así nunca
    aparece una imagen rota.
    """
    return {"logo_url": _buscar_logo()}
