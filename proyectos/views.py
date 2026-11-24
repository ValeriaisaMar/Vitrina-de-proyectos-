"""Vistas de los estudiantes para sus proyectos: listar, crear, editar y eliminar."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from cuentas.decoradores import rol_requerido
from cuentas.models import Rol
from proyectos.forms import FormularioProyecto
from proyectos.models import Proyecto
from proyectos.permisos import puede_editar, puede_eliminar


@rol_requerido(Rol.ESTUDIANTE)
def mis_proyectos(request):
    """Proyectos en los que el estudiante es autor o coautor."""
    proyectos = (
        Proyecto.objects.de_autor(request.user)
        .select_related("asignatura")
        .prefetch_related("autorias")
        .order_by("-actualizado_en")
    )
    filas = [
        {"proyecto": p, "editable": puede_editar(request.user, p), "eliminable": puede_eliminar(request.user, p)}
        for p in proyectos
    ]
    return render(request, "proyectos/mis_proyectos.html", {"filas": filas})


@rol_requerido(Rol.ESTUDIANTE)
def crear(request):
    """Crea un proyecto en Borrador con el estudiante como creador."""
    form = FormularioProyecto(request.POST or None, request.FILES or None, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():  # o se guarda todo (proyecto, autores, imágenes) o nada
            proyecto = form.save()
        messages.success(request, _("Proyecto creado. Quedó guardado como borrador."))
        return redirect(proyecto.get_absolute_url())
    return render(request, "proyectos/formulario.html", {"form": form, "es_nuevo": True})


@login_required
def editar(request, slug):
    """Edita un proyecto propio mientras esté en Borrador o Con observaciones."""
    proyecto = get_object_or_404(Proyecto, slug=slug)
    if not puede_editar(request.user, proyecto):
        raise PermissionDenied
    form = FormularioProyecto(request.POST or None, request.FILES or None, instance=proyecto, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, _("Guardamos los cambios del proyecto."))
        return redirect(proyecto.get_absolute_url())
    return render(request, "proyectos/formulario.html", {"form": form, "proyecto": proyecto, "es_nuevo": False})


@login_required
def eliminar(request, slug):
    """Pide confirmación (GET) y elimina (POST) un borrador del que el usuario es creador."""
    proyecto = get_object_or_404(Proyecto, slug=slug)
    if not puede_eliminar(request.user, proyecto):
        raise PermissionDenied
    if request.method == "POST":
        titulo = proyecto.titulo
        _borrar_archivos(proyecto)
        proyecto.delete()
        messages.success(request, _("Eliminamos el proyecto «%(titulo)s».") % {"titulo": titulo})
        return redirect("proyectos:mis_proyectos")
    return render(request, "proyectos/confirmar_eliminar.html", {"proyecto": proyecto})


def _borrar_archivos(proyecto):
    """Borrar un registro no borra sus archivos del disco; aquí se hace a mano."""
    if proyecto.documento_pdf:
        proyecto.documento_pdf.delete(save=False)
    for imagen in proyecto.imagenes.all():
        imagen.archivo.delete(save=False)
