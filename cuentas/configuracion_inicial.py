"""Configuración inicial: crear el primer admin desde el navegador (spec 010).

Mientras no haya ningún admin activo, /configuracion-inicial/ permite crear el primer admin. Para
que un desconocido no se adueñe de una instalación recién publicada, pide un código de un solo uso
que solo ve quien tiene acceso al servidor:

- el comando `python manage.py codigo_configuracion_inicial` lo imprime en la terminal, o
- al abrir la página sin un código vigente, el servidor genera uno y lo escribe en el log.

Del código solo se guarda su huella SHA-256 (ConfiguracionInicial.hash_codigo). Vence a los 30
minutos, sirve una sola vez y se invalida tras 5 intentos fallidos.

Este módulo es la única puerta: lo usan la vista, el comando, el enlace de Entrar y las pruebas.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from cuentas.models import ConfiguracionInicial, Rol, Usuario

logger = logging.getLogger("cuentas.configuracion_inicial")

# Sin 0/O ni 1/I/L, que se confunden al copiarlos a mano: 31 símbolos.
ALFABETO = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
LARGO_CODIGO = 12
MINUTOS_VIGENCIA = 30
MAXIMO_FALLOS = 5
RUTA = "/configuracion-inicial/"
MOTIVO = "Configuración inicial"  # queda en CambioRol.motivo (es un dato, no se traduce)

CLAVE_CACHE = "configuracion_inicial:hay_admin"
SEGUNDOS_CACHE = 60


# --------------------------------------------------------------------------- ¿Hay un admin activo?


def hay_admin_activo():
    """True si existe una cuenta activa con el rol admin. Consulta siempre la base de datos.

    La usan la página, el comando y la creación del admin: lo que decide el acceso nunca sale
    de la caché.
    """
    return Usuario.objects.filter(is_active=True, roles_asignados__rol=Rol.ADMIN).exists()


def hay_admin_activo_en_cache():
    """Lo mismo, pero guardado en la caché 60 segundos. Solo para mostrar el enlace en Entrar.

    Las señales (cuentas/signals.py) borran el valor cuando cambian roles o cuentas. Como la caché
    en memoria es de cada proceso del servidor, además vence sola: un enlace mostrado unos segundos
    de más solo lleva a un 404.
    """
    return cache.get_or_set(CLAVE_CACHE, hay_admin_activo, SEGUNDOS_CACHE)


def olvidar_cache():
    """Borra el valor guardado para que la próxima visita a Entrar lo vuelva a calcular."""
    cache.delete(CLAVE_CACHE)


# --------------------------------------------------------------------------- El código


def normalizar(codigo):
    """Quita guiones y espacios y pasa a mayúsculas: «7k4q m2xp-9wda» → «7K4QM2XP9WDA»."""
    return "".join((codigo or "").split()).replace("-", "").upper()


def formatear(codigo):
    """Muestra el código en grupos de 4: «7K4Q-M2XP-9WDA»."""
    return "-".join(codigo[i:i + 4] for i in range(0, len(codigo), 4))


def _huella(codigo):
    return hashlib.sha256(normalizar(codigo).encode()).hexdigest()


def url_configuracion(request=None):
    """Dirección completa de la página: SITIO_URL si está configurada, si no la de la petición o solo la ruta."""
    if settings.SITIO_URL:
        return settings.SITIO_URL + RUTA
    if request is not None:
        return request.build_absolute_uri(RUTA)
    return RUTA


def bloque(codigo, url):
    """Texto fácil de ver en la terminal o en el log con el código y dónde usarlo."""
    return (
        "==== VITRINA: CÓDIGO DE CONFIGURACIÓN INICIAL ====\n"
        f"Código: {formatear(codigo)}   (vence en {MINUTOS_VIGENCIA} minutos)\n"
        f"Ábrelo en: {url}\n"
        "==================================================="
    )


def generar_codigo(url=RUTA, en_el_log=True):
    """Crea un código nuevo (el anterior deja de servir) y lo devuelve.

    Con en_el_log=True escribe el bloque con el código en el log (respaldo de la página). El
    comando lo imprime él mismo en la terminal y solo deja en el log un aviso sin el código.
    El código en claro solo existe en la respuesta de esta función: en la base queda su huella.
    """
    codigo = "".join(secrets.choice(ALFABETO) for _ in range(LARGO_CODIGO))
    ahora = timezone.now()
    configuracion = ConfiguracionInicial.obtener()
    configuracion.hash_codigo = _huella(codigo)
    configuracion.creado_en = ahora
    configuracion.vence_en = ahora + timedelta(minutes=MINUTOS_VIGENCIA)
    configuracion.intentos_fallidos = 0
    configuracion.save()
    if en_el_log:
        logger.warning("\n%s", bloque(codigo, url))
    else:
        logger.warning("Se generó un código de configuración inicial desde el comando (el anterior ya no sirve).")
    return codigo


def asegurar_codigo(url=RUTA):
    """Respaldo por logs: si no hay un código vigente, genera uno. Si ya hay, no lo toca.

    Así recargar la página no invalida el código que alguien acaba de copiar del log.
    Devuelve True si generó uno.
    """
    if ConfiguracionInicial.obtener().codigo_vigente:
        return False
    generar_codigo(url)
    return True


def codigo_correcto(configuracion, codigo):
    """True si el código coincide con el vigente. compare_digest tarda lo mismo acierte o no."""
    if not configuracion.codigo_vigente or not codigo:
        return False
    return hmac.compare_digest(configuracion.hash_codigo, _huella(codigo))


def registrar_fallo(configuracion):
    """Suma un intento fallido; al llegar a MAXIMO_FALLOS invalida el código y lo avisa en el log."""
    if not configuracion.hash_codigo:
        return
    configuracion.intentos_fallidos += 1
    if configuracion.intentos_fallidos >= MAXIMO_FALLOS:
        configuracion.hash_codigo = ""
        logger.warning(
            "Se invalidó el código de configuración inicial tras %s intentos fallidos. "
            "Genera otro con: python manage.py codigo_configuracion_inicial",
            configuracion.intentos_fallidos,
        )
    configuracion.save(update_fields=["intentos_fallidos", "hash_codigo"])


def invalidar_codigo(completada=False):
    """Borra el código vigente (y marca la configuración como completada si se indica)."""
    configuracion = ConfiguracionInicial.obtener()
    configuracion.hash_codigo = ""
    if completada:
        configuracion.completada_en = timezone.now()
    configuracion.save(update_fields=["hash_codigo", "completada_en"])


# --------------------------------------------------------------------------- Crear el primer admin (historia 3)

CLAVE_PRIMEROS_PASOS = "primeros_pasos"  # en la sesión: el panel del admin muestra los siguientes pasos


class ConfiguracionNoDisponible(Exception):
    """Ya hay un admin activo (por ejemplo, otro envío llegó primero)."""


class DatosInvalidos(Exception):
    """El código no sirve o los datos de la cuenta existente no son correctos (mensaje genérico)."""


class CorreoYaRegistrado(Exception):
    """Con el código correcto, se pidió crear una cuenta con un correo que ya existe."""


def _cuenta_existente(email, password):
    """La cuenta con ese correo si la contraseña es correcta; si no, None.

    No se usa authenticate() porque rechaza cuentas inactivas, y una cuenta que nunca se activó
    también puede ser la del primer admin. Si el correo no existe se calcula igual un hash de la
    contraseña, para que la respuesta tarde lo mismo y no delate qué correos tienen cuenta.
    """
    usuario = Usuario.objects.filter(email__iexact=Usuario.objects.normalizar_correo(email)).first()
    if usuario is None:
        Usuario().set_password(password)
        return None
    return usuario if usuario.check_password(password) else None


def crear_primer_admin(codigo, opcion, datos):
    """Crea una cuenta admin nueva (opcion="nueva") o promueve una existente (opcion="existente").

    datos: nombres, apellidos, email y password1 (nueva) o email y password (existente).
    Devuelve el usuario. Lanza ConfiguracionNoDisponible, DatosInvalidos o CorreoYaRegistrado.

    Todo ocurre en una transacción con la fila de ConfiguracionInicial bloqueada
    (select_for_update): si dos personas envían el formulario a la vez, la segunda espera a que
    termine la primera y, al volver a comprobar dentro del bloqueo, ve que ya hay un admin.
    """
    from cuentas.models import CambioRol
    from cuentas.roles import dar_rol

    ConfiguracionInicial.obtener()  # la fila debe existir para poder bloquearla
    fallo = None
    usuario = None
    with transaction.atomic():
        configuracion = ConfiguracionInicial.objects.select_for_update().get(pk=1)
        if hay_admin_activo():
            raise ConfiguracionNoDisponible
        if not codigo_correcto(configuracion, codigo):
            # Un error lanzado aquí desharía también el conteo del fallo: se anota y se lanza al salir.
            registrar_fallo(configuracion)
            fallo = DatosInvalidos()
        elif opcion == "nueva":
            email = Usuario.objects.normalizar_correo(datos["email"])
            if Usuario.objects.filter(email__iexact=email).exists():
                fallo = CorreoYaRegistrado()
            else:
                # Activa sin enlace de activación: quien tiene el código tiene acceso al servidor
                usuario = Usuario.objects.create_user(
                    email=email, password=datos["password1"], nombres=datos["nombres"],
                    apellidos=datos["apellidos"], roles=[Rol.ADMIN], is_active=True,
                )
                CambioRol.objects.create(usuario=usuario, rol=Rol.ADMIN, accion=CambioRol.Accion.AGREGADO,
                                         hecho_por=None, motivo=MOTIVO)
        else:
            usuario = _cuenta_existente(datos["email"], datos["password"])
            if usuario is None:
                fallo = DatosInvalidos()
            else:
                if not usuario.is_active:
                    usuario.is_active = True
                    usuario.save(update_fields=["is_active"])
                dar_rol(usuario, Rol.ADMIN, actor=None, motivo=MOTIVO)  # conserva sus otros roles

        if fallo is None:
            configuracion.hash_codigo = ""  # un solo uso
            configuracion.completada_en = timezone.now()
            configuracion.save(update_fields=["hash_codigo", "completada_en"])
    if fallo is not None:
        raise fallo

    olvidar_cache()
    logger.info("Configuración inicial completada: admin %s (%s).", usuario.email,
                "cuenta nueva" if opcion == "nueva" else "cuenta existente")
    return usuario


def al_crear_superusuario(usuario):
    """createsuperuser (camino por consola): deja el motivo en el registro, invalida el código y la caché."""
    from cuentas.models import CambioRol

    if usuario.tiene_rol(Rol.ADMIN):
        CambioRol.objects.create(usuario=usuario, rol=Rol.ADMIN, accion=CambioRol.Accion.AGREGADO,
                                 hecho_por=None, motivo=MOTIVO)
    invalidar_codigo(completada=True)
    olvidar_cache()
