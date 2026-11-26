"""Dar y quitar roles (spec 008, historia 1).

Esta es la única puerta para cambiar los roles de una persona: así las reglas se cumplen siempre,
se cambie desde la gestión de usuarios, desde un comando o desde una prueba.

Reglas:
- Todo usuario conserva al menos un rol.
- No se le puede quitar el rol admin al último admin activo.
- Cada rol que se da o se quita queda en CambioRol con quién lo hizo y cuándo.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from cuentas.models import JERARQUIA, CambioRol, Rol, RolAsignado, Usuario

CLAVE_SESION = "rol_activo"


def ordenar(roles):
    """Ordena una colección de roles de menor a mayor privilegio, sin repetidos."""
    conjunto = set(roles)
    return [rol.value for rol in JERARQUIA if rol in conjunto]


def es_ultimo_admin(usuario):
    """True si es la única cuenta activa con el rol admin."""
    otros = Usuario.objects.filter(is_active=True, roles_asignados__rol=Rol.ADMIN).exclude(pk=usuario.pk)
    return usuario.is_active and usuario.tiene_rol(Rol.ADMIN) and not otros.exists()


def validar_roles(usuario, nuevos):
    """Lanza ValidationError si el cambio deja a la persona sin roles o a la plataforma sin admin."""
    nuevos = set(nuevos)
    if not nuevos:
        raise ValidationError(_("Toda cuenta necesita al menos un rol."), code="sin_roles")
    if Rol.ADMIN not in nuevos and es_ultimo_admin(usuario):
        raise ValidationError(
            _("No puedes quitarle el rol admin: es la única cuenta admin activa. Primero nombra a otro admin."),
            code="ultimo_admin",
        )


def asignar_roles(usuario, nuevos, actor, motivo=""):
    """Deja a la persona exactamente con los roles indicados. Devuelve (agregados, quitados).

    motivo queda en cada CambioRol cuando no lo decide un admin (spec 010: "Configuración inicial").

    Todo ocurre en una transacción: las filas de los admins se bloquean para que dos admins que
    se quitan el rol a la vez no dejen la plataforma sin ninguno.
    """
    nuevos = ordenar(nuevos)
    with transaction.atomic():
        list(RolAsignado.objects.select_for_update().filter(rol=Rol.ADMIN))  # bloqueo
        usuario.olvidar_roles()
        validar_roles(usuario, nuevos)
        actuales = set(usuario.roles)
        agregados = [rol for rol in nuevos if rol not in actuales]
        quitados = [rol for rol in ordenar(actuales) if rol not in nuevos]

        if quitados:
            RolAsignado.objects.filter(usuario=usuario, rol__in=quitados).delete()
        for rol in agregados:
            RolAsignado.objects.create(usuario=usuario, rol=rol, asignado_por=actor)
        CambioRol.objects.bulk_create(
            [CambioRol(usuario=usuario, rol=rol, accion=CambioRol.Accion.AGREGADO, hecho_por=actor, motivo=motivo)
             for rol in agregados]
            + [CambioRol(usuario=usuario, rol=rol, accion=CambioRol.Accion.QUITADO, hecho_por=actor, motivo=motivo)
               for rol in quitados]
        )
    usuario.olvidar_roles()
    return agregados, quitados


def dar_rol(usuario, rol, actor=None, motivo=""):
    """Agrega un rol si la persona todavía no lo tiene (por ejemplo, al registrarse)."""
    if not usuario.tiene_rol(rol):
        asignar_roles(usuario, set(usuario.roles) | {rol}, actor, motivo)


def resumen(agregados, quitados):
    """Texto para el registro de acciones, por ejemplo: «Roles: + Profesor; − Estudiante»."""
    partes = [f"+ {Rol(r).label}" for r in agregados] + [f"− {Rol(r).label}" for r in quitados]
    return "Roles: " + "; ".join(partes) if partes else ""


def activar_rol(request, rol):
    """Cambia el rol con el que actúa la persona. Devuelve False si no tiene ese rol."""
    usuario = request.user
    if not usuario.tiene_rol(rol):
        return False
    request.session[CLAVE_SESION] = rol
    usuario.rol_activo = rol
    if usuario.ultimo_rol != rol:
        usuario.ultimo_rol = rol
        usuario.save(update_fields=["ultimo_rol"])
    return True
