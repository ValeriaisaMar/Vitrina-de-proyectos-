"""Límite de intentos fallidos al iniciar sesión (constitución, principio IV).

Tras MAXIMO_INTENTOS fallos con el mismo correo desde la misma IP, ese correo queda bloqueado
desde esa IP durante BLOQUEO_SEGUNDOS. Los intentos se cuentan en la caché de Django: es rápido,
se borra solo al vencer y no necesita tablas.
"""

from django.core.cache import cache

MAXIMO_INTENTOS = 5
BLOQUEO_SEGUNDOS = 15 * 60


def _clave(email, ip):
    return f"login:{(email or '').strip().lower()}:{ip or 'sin-ip'}"


def ip_de(request):
    """Dirección IP de quien hace la petición."""
    return request.META.get("REMOTE_ADDR", "")


def esta_bloqueado(email, ip):
    """True si ese correo ya alcanzó el máximo de intentos fallidos desde esa IP."""
    return cache.get(_clave(email, ip), 0) >= MAXIMO_INTENTOS


def registrar_fallo(email, ip):
    """Suma un intento fallido. El conteo se borra solo pasados BLOQUEO_SEGUNDOS."""
    clave = _clave(email, ip)
    if cache.add(clave, 1, BLOQUEO_SEGUNDOS):  # add solo crea la clave si no existía
        return 1
    try:
        return cache.incr(clave)
    except ValueError:  # la clave venció justo entre add e incr
        cache.set(clave, 1, BLOQUEO_SEGUNDOS)
        return 1


def limpiar(email, ip):
    """Borra el conteo (se llama al iniciar sesión correctamente)."""
    cache.delete(_clave(email, ip))
