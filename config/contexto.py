"""Procesadores de contexto: datos que todas las plantillas reciben automáticamente."""

from django.contrib.staticfiles import finders
from django.templatetags.static import static

# Nombres de archivo que se buscan en static/img/, en este orden.
_LOGOS_POSIBLES = ("img/logo-uteq.svg", "img/logo-uteq.png", "img/logo-uteq.webp")
_LOGOS_BLANCOS = ("img/logo-uteq-blanco.svg", "img/logo-uteq-blanco.png", "img/logo-uteq-blanco.webp")


def _buscar(rutas):
    for ruta in rutas:
        if finders.find(ruta):
            return static(ruta)
    return None


def _buscar_logo():
    return _buscar(_LOGOS_POSIBLES)


def _webp(url):
    """La versión .webp de un logo .png, si existe junto a él (para <picture>)."""
    if url and url.endswith(".png"):
        ruta = url.split("/static/", 1)[-1][:-4] + ".webp"
        if finders.find(ruta):
            return static(ruta)
    return None


def marca(request):
    """Entrega las URL del logo (modo claro y modo oscuro) si están en static/img/; si no, None.

    Las plantillas muestran el nombre de la plataforma en texto cuando no hay logo, así nunca
    aparece una imagen rota. El logo blanco es para el modo oscuro; si falta, se usa el normal.
    """
    logo = _buscar_logo()
    blanco = _buscar(_LOGOS_BLANCOS) or logo
    return {
        "logo_url": logo,
        "logo_webp_url": _webp(logo),
        "logo_blanco_url": blanco,
        "logo_blanco_webp_url": _webp(blanco),
    }


def roles(request):
    """El rol con el que actúa la persona y los que puede elegir en el encabezado (spec 008)."""
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    from cuentas.models import Rol  # import local: este módulo se carga antes que las apps

    return {
        "rol_activo": usuario.rol_activo,
        "rol_activo_etiqueta": Rol(usuario.rol_activo).label,
        "roles_disponibles": [(rol, Rol(rol).label) for rol in usuario.roles],
    }
