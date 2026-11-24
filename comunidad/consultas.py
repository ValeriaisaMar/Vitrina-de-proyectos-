"""Lo que la ficha de un proyecto necesita saber de su comunidad."""

from comunidad.forms import FormularioComentario
from comunidad.models import Comentario
from comunidad.permisos import puede_moderar


def datos_comunidad(usuario, proyecto, form=None):
    """Totales, lo que ya hizo esta persona y los comentarios que le corresponde ver.

    Los moderadores (autores y admins) ven también los comentarios ocultos, marcados.
    """
    moderador = puede_moderar(usuario, proyecto)
    comentarios = Comentario.objects.filter(proyecto=proyecto).select_related("autor")
    if not moderador:
        comentarios = comentarios.visibles()
    con_sesion = usuario.is_authenticated
    return {
        "total_me_gusta": proyecto.me_gustas.count(),
        "le_gusta": con_sesion and proyecto.me_gustas.filter(usuario=usuario).exists(),
        "es_favorito": con_sesion and proyecto.favoritos.filter(usuario=usuario).exists(),
        "puede_dar_me_gusta": con_sesion and not proyecto.es_autor(usuario),
        "moderador": moderador,
        "ids_autores": set(proyecto.autorias.values_list("usuario_id", flat=True)),
        "comentarios": comentarios,
        "form": form or FormularioComentario(),
    }
