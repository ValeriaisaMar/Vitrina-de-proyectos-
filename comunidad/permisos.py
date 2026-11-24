"""Quién puede moderar o borrar comentarios (constitución, principio V)."""

from cuentas.models import Rol


def puede_moderar(usuario, proyecto):
    """Ocultar o mostrar comentarios: los autores del proyecto y los admins."""
    return usuario.is_authenticated and (usuario.rol == Rol.ADMIN or proyecto.es_autor(usuario))


def puede_borrar(usuario, comentario):
    """Borrar un comentario: solo quien lo escribió."""
    return usuario.is_authenticated and comentario.autor_id == usuario.pk
