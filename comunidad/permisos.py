"""Quién puede moderar, borrar o responder comentarios (constitución, principio V)."""

from cuentas.models import Rol


def puede_moderar(usuario, proyecto):
    """Ocultar o mostrar comentarios: los autores del proyecto y quien actúa como admin."""
    return usuario.is_authenticated and (usuario.rol_activo == Rol.ADMIN or proyecto.es_autor(usuario))


def puede_borrar(usuario, comentario):
    """Borrar un comentario: solo quien lo escribió."""
    return usuario.is_authenticated and comentario.autor_id == usuario.pk


def puede_responder(usuario, comentario, ids_autores=None):
    """Responder un comentario (spec 008): solo los autores del proyecto.

    Un solo nivel: no se responde a una respuesta. Tampoco a un comentario oculto.
    ids_autores evita una consulta por comentario cuando ya se conocen los autores.
    """
    if not usuario.is_authenticated or comentario.respuesta_a_id is not None or comentario.oculto:
        return False
    if ids_autores is not None:
        return usuario.pk in ids_autores
    return comentario.proyecto.es_autor(usuario)
