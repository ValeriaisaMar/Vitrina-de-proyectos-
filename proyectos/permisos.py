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
    return usuario.rol in (Rol.PROFESOR, Rol.ADMIN) or proyecto.es_autor(usuario)


def puede_editar(usuario, proyecto):
    """Cualquier autor, solo en Borrador o Con observaciones."""
    return usuario.is_authenticated and proyecto.editable and proyecto.es_autor(usuario)


def puede_eliminar(usuario, proyecto):
    """Solo el creador, y solo mientras el proyecto no haya salido de Borrador."""
    return (
        usuario.is_authenticated
        and proyecto.estado == Estado.BORRADOR
        and proyecto.autorias.filter(usuario=usuario, es_creador=True).exists()
    )
