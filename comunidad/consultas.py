"""Lo que la ficha de un proyecto necesita saber de su comunidad."""

from django.db.models import Prefetch

from comunidad.forms import FormularioComentario
from comunidad.models import Comentario
from comunidad.permisos import puede_moderar


def datos_comunidad(usuario, proyecto, form=None):
    """Totales, lo que ya hizo esta persona y los comentarios que le corresponde ver.

    - Los moderadores (autores y admins) ven también los comentarios ocultos, marcados.
    - Las respuestas de los autores llegan con los comentarios en una sola consulta extra
      (Prefetch), y los ids de los autores se calculan una vez: así no hay consultas N+1.
    """
    moderador = puede_moderar(usuario, proyecto)
    ids_autores = set(proyecto.autorias.values_list("usuario_id", flat=True))

    respuestas = Comentario.objects.select_related("autor").order_by("creado_en", "id")
    comentarios = Comentario.objects.filter(proyecto=proyecto).principales().select_related("autor")
    if not moderador:
        # Ocultar un comentario oculta también su hilo: sus respuestas ya no se muestran
        comentarios = comentarios.visibles()
        respuestas = respuestas.visibles()
    comentarios = comentarios.prefetch_related(Prefetch("respuestas", queryset=respuestas, to_attr="hilo"))

    con_sesion = usuario.is_authenticated
    comentarios = list(comentarios)
    for comentario in comentarios:  # marca quién es autor del proyecto, sin consultas extra
        comentario.es_de_autor = comentario.autor_id in ids_autores
        for respuesta in comentario.hilo:
            respuesta.es_de_autor = respuesta.autor_id in ids_autores
    return {
        "total_me_gusta": proyecto.me_gustas.count(),
        "le_gusta": con_sesion and proyecto.me_gustas.filter(usuario=usuario).exists(),
        "es_favorito": con_sesion and proyecto.favoritos.filter(usuario=usuario).exists(),
        "puede_dar_me_gusta": con_sesion and usuario.pk not in ids_autores,
        "moderador": moderador,
        "ids_autores": ids_autores,
        "revisor_id": proyecto.revisor_id,
        # Solo los autores responden: el botón "Responder" sale si quien mira es autor
        "puede_responder": con_sesion and usuario.pk in ids_autores,
        "comentarios": comentarios,
        "total_comentarios": len(comentarios) + sum(len(c.hilo) for c in comentarios),
        "form": form or FormularioComentario(),
    }
