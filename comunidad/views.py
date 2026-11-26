"""Vistas de comunidad: me gusta, guardados y comentarios.

Todas las acciones son POST (cambian datos), van protegidas con CSRF y redirigen a la ficha del
proyecto, así funcionan sin JavaScript. Solo existen sobre proyectos aprobados.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from comunidad.forms import FormularioComentario
from comunidad.models import Comentario, Guardado, MeGusta
from comunidad.correos import avisar_respuesta
from comunidad.permisos import puede_borrar, puede_moderar, puede_responder
from proyectos.models import Proyecto

MAX_COMENTARIOS = 5          # por persona...
VENTANA_SEGUNDOS = 10 * 60   # ...cada 10 minutos


def _publicado(slug):
    return get_object_or_404(Proyecto.objects.publicados(), slug=slug)


def _volver(proyecto, ancla="comunidad"):
    return redirect(f"{proyecto.get_absolute_url()}#{ancla}")


def _interruptor(modelo, usuario, proyecto):
    """Si existe lo quita; si no, lo crea. Devuelve True si quedó puesto.

    Si dos clics llegan a la vez, la restricción única de la base rechaza el segundo
    (IntegrityError) y simplemente lo ignoramos: el resultado es el mismo.
    """
    borrados, _detalle = modelo.objects.filter(usuario=usuario, proyecto=proyecto).delete()
    if borrados:
        return False
    try:
        with transaction.atomic():
            modelo.objects.create(usuario=usuario, proyecto=proyecto)
    except IntegrityError:
        pass
    return True


@login_required
@require_POST
def me_gusta(request, slug):
    proyecto = _publicado(slug)
    if proyecto.es_autor(request.user):
        messages.info(request, _("No puedes dar me gusta a tu propio proyecto."))
    else:
        _interruptor(MeGusta, request.user, proyecto)
    return _volver(proyecto)


@login_required
@require_POST
def guardar(request, slug):
    """Guarda o quita el proyecto de "Guardados" (un mismo botón pone y quita)."""
    proyecto = _publicado(slug)
    if _interruptor(Guardado, request.user, proyecto):
        messages.success(request, _("Proyecto guardado. Lo encuentras en Guardados."))
    else:
        messages.info(request, _("Quitaste el proyecto de Guardados."))
    if request.POST.get("volver") in ("guardados", "favoritos"):
        return redirect("comunidad:guardados")
    return _volver(proyecto)


@login_required
def guardados(request):
    """Proyectos guardados por esta persona (solo los que siguen publicados)."""
    proyectos = (
        Proyecto.objects.publicados()
        .filter(guardados__usuario=request.user)
        .select_related("asignatura", "periodo").prefetch_related("tecnologias", "imagenes")
        .order_by("-guardados__creado_en")
    )
    return render(request, "comunidad/guardados.html", {"proyectos": proyectos})


def _limite_superado(usuario):
    """Cuenta los comentarios de la persona en una ventana de 10 minutos (en la caché)."""
    clave = f"comentarios:{usuario.pk}"
    cache.add(clave, 0, VENTANA_SEGUNDOS)  # crea el contador solo si no existe
    return cache.incr(clave) > MAX_COMENTARIOS


@login_required
@require_POST
def comentar(request, slug):
    proyecto = _publicado(slug)
    form = FormularioComentario(request.POST)
    if not form.is_valid():
        for error in form.errors.get("texto", []):
            messages.error(request, error)
        return _volver(proyecto, "comentar")
    if _limite_superado(request.user):
        messages.error(request, _("Publicaste varios comentarios seguidos. Espera unos minutos e intenta de nuevo."))
        return _volver(proyecto, "comentar")
    comentario = form.save(commit=False)
    comentario.proyecto = proyecto
    comentario.autor = request.user
    comentario.save()
    return _volver(proyecto, f"comentario-{comentario.pk}")


@login_required
@require_POST
def ocultar(request, pk):
    """Oculta o vuelve a mostrar un comentario. Solo autores del proyecto y admins."""
    comentario = get_object_or_404(Comentario.objects.select_related("proyecto"), pk=pk, proyecto__estado="aprobado")
    if not puede_moderar(request.user, comentario.proyecto):
        raise PermissionDenied
    comentario.oculto = not comentario.oculto
    comentario.ocultado_por = request.user if comentario.oculto else None
    comentario.ocultado_en = timezone.now() if comentario.oculto else None
    comentario.save(update_fields=["oculto", "ocultado_por", "ocultado_en"])
    messages.success(request, _("Comentario oculto.") if comentario.oculto else _("Comentario visible de nuevo."))
    return _volver(comentario.proyecto, f"comentario-{comentario.pk}")


@login_required
@require_POST
def borrar(request, pk):
    """Quien escribió un comentario puede borrarlo."""
    comentario = get_object_or_404(Comentario.objects.select_related("proyecto"), pk=pk)
    if not puede_borrar(request.user, comentario):
        raise PermissionDenied
    proyecto = comentario.proyecto
    comentario.delete()
    messages.success(request, _("Borramos tu comentario."))
    return _volver(proyecto)


@login_required
@require_POST
def responder(request, pk):
    """Un autor del proyecto responde un comentario (spec 008). Un solo nivel de respuesta."""
    padre = get_object_or_404(Comentario.objects.select_related("proyecto", "autor"), pk=pk, proyecto__estado="aprobado")
    if not puede_responder(request.user, padre):
        raise PermissionDenied
    proyecto = padre.proyecto
    form = FormularioComentario(request.POST)
    if not form.is_valid():
        for error in form.errors.get("texto", []):
            messages.error(request, error)
        return _volver(proyecto, f"comentario-{padre.pk}")
    if _limite_superado(request.user):
        messages.error(request, _("Publicaste varios comentarios seguidos. Espera unos minutos e intenta de nuevo."))
        return _volver(proyecto, f"comentario-{padre.pk}")
    respuesta = form.save(commit=False)
    respuesta.proyecto = proyecto
    respuesta.autor = request.user
    respuesta.respuesta_a = padre
    respuesta.full_clean()  # valida en el modelo que sea de un solo nivel
    respuesta.save()
    if padre.autor_id != request.user.pk:
        avisar_respuesta(request, padre, respuesta)
    return _volver(proyecto, f"comentario-{respuesta.pk}")
