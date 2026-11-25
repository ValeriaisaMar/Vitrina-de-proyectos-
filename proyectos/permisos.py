"""Reglas de quién puede hacer qué con un proyecto (constitución, principio V).

Se usan en las vistas (para responder 403) y en las plantillas (para mostrar u ocultar
botones). Ocultar un botón nunca reemplaza la comprobación en la vista.
"""

from cuentas.models import Rol
from proyectos.models import Estado


def puede_ver(usuario, proyecto):
    """Aprobado: cualquiera. Si no: sus autores, los profesores y los admins (vista previa)."""
    if proyecto.publicado:
        return True
    if not usuario.is_authenticated:
        return False
    return usuario.es_docente or proyecto.es_autor(usuario)


def _actua_como_estudiante(usuario):
    """Las acciones de autor (editar, enviar, salir…) son del rol estudiante (spec 008)."""
    return usuario.is_authenticated and usuario.rol_activo == Rol.ESTUDIANTE


def puede_editar(usuario, proyecto):
    """Cualquier autor, solo en Borrador o Con observaciones."""
    return _actua_como_estudiante(usuario) and proyecto.editable and proyecto.es_autor(usuario)


def puede_eliminar(usuario, proyecto):
    """Solo el creador, y solo mientras el proyecto no haya salido de Borrador."""
    return (
        _actua_como_estudiante(usuario)
        and proyecto.estado == Estado.BORRADOR
        and proyecto.autorias.filter(usuario=usuario, es_creador=True).exists()
    )


def puede_salir(usuario, proyecto):
    """Un coautor (no el creador) puede dejar el proyecto mientras se pueda editar.

    Después de enviado ya no: la autoría de un proyecto en revisión o aprobado es parte de lo
    que se certifica. El creador no puede salir; si ya no quiere el proyecto, lo elimina.
    """
    return (
        _actua_como_estudiante(usuario)
        and proyecto.editable
        and proyecto.autorias.filter(usuario=usuario, es_creador=False).exists()
    )


def puede_transferir(usuario, proyecto):
    """El creador puede pasarle el proyecto a un coautor mientras se pueda editar.

    Hace falta al menos un coautor con cuenta activa que lo reciba.
    """
    return (
        _actua_como_estudiante(usuario)
        and proyecto.editable
        and proyecto.autorias.filter(usuario=usuario, es_creador=True).exists()
        and proyecto.autorias.filter(es_creador=False, usuario__is_active=True).exists()
    )


def puede_ver_historial(usuario, proyecto):
    """El historial lo ven los autores, los profesores y los admins; el público no."""
    if not usuario.is_authenticated:
        return False
    return usuario.es_docente or proyecto.es_autor(usuario)

