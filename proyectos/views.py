"""Vistas de proyectos.

- Estudiantes: listar, crear, editar, eliminar y enviar a revisión.
- Profesores y admins: bandeja, tomar y revisar (módulo 004).

Ninguna vista cambia proyecto.estado directamente: todas llaman a servicios.cambiar_estado().
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Max, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from cuentas.decoradores import rol_requerido
from cuentas.models import Rol
from proyectos.correos import avisar_decision
from proyectos.forms import FormularioDecision, FormularioEnvio, FormularioProyecto
from proyectos.models import ESTADOS_DE_DECISION, Estado, EventoEstado, Proyecto
from proyectos.permisos import puede_editar, puede_eliminar
from proyectos.servicios import TransicionNoPermitida, cambiar_estado, puede_cambiar


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
        {
            "proyecto": p,
            "editable": puede_editar(request.user, p),
            "eliminable": puede_eliminar(request.user, p),
            "enviable": puede_cambiar(request.user, p, Estado.ENVIADO),
        }
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


# --------------------------------------------------------------------------- Enviar (autores)


@login_required
def enviar(request, slug):
    """Pide confirmación (GET) y envía (POST) un proyecto a revisión. También sirve para reenviar."""
    proyecto = get_object_or_404(Proyecto, slug=slug)
    if not puede_cambiar(request.user, proyecto, Estado.ENVIADO):
        raise PermissionDenied
    reenvio = proyecto.estado == Estado.CON_OBSERVACIONES
    form = FormularioEnvio(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            cambiar_estado(proyecto, Estado.ENVIADO, request.user, form.cleaned_data["comentario"])
        except TransicionNoPermitida:
            messages.error(request, _("El proyecto cambió de estado mientras tanto. Revisa cómo quedó."))
        else:
            messages.success(request, _("Enviamos tu proyecto a revisión. Te avisaremos por correo cuando un docente decida."))
        return redirect(proyecto.get_absolute_url())
    return render(request, "proyectos/enviar.html", {
        "form": form,
        "proyecto": proyecto,
        "reenvio": reenvio,
        "observacion": proyecto.ultima_decision if reenvio else None,
    })


# --------------------------------------------------------------------------- Bandeja (docentes)

VISTAS_BANDEJA = ("pendientes", "en_revision", "decididos")


def _consultas_bandeja(usuario):
    """Las tres listas de la bandeja. Cada proyecto trae la fecha que importa en esa lista."""
    base = Proyecto.objects.select_related("asignatura", "revisor").prefetch_related("autores")
    eventos_a = lambda estado: Q(eventos__estado_nuevo=estado)  # noqa: E731

    pendientes = (
        base.filter(estado=Estado.ENVIADO)
        .annotate(fecha=Max("eventos__creado_en", filter=eventos_a(Estado.ENVIADO)),
                  envios=Count("eventos", filter=eventos_a(Estado.ENVIADO)))
        .order_by("fecha")  # los que más tiempo llevan esperando, primero
    )

    en_revision = base.filter(estado=Estado.EN_REVISION)
    if usuario.rol == Rol.PROFESOR:
        en_revision = en_revision.filter(revisor=usuario)  # el admin ve todos
    en_revision = en_revision.annotate(
        fecha=Max("eventos__creado_en", filter=eventos_a(Estado.EN_REVISION))
    ).order_by("fecha")

    mis_decisiones = Q(eventos__actor=usuario, eventos__estado_nuevo__in=ESTADOS_DE_DECISION)
    decididos = (
        base.filter(pk__in=EventoEstado.objects.filter(actor=usuario, estado_nuevo__in=ESTADOS_DE_DECISION).values("proyecto"))
        .annotate(fecha=Max("eventos__creado_en", filter=mis_decisiones))
        .order_by("-fecha")
    )
    return {"pendientes": pendientes, "en_revision": en_revision, "decididos": decididos}


@rol_requerido(Rol.PROFESOR, Rol.ADMIN)
def bandeja(request):
    """Bandeja común de revisión: por revisar, en revisión y decididos por mí."""
    vista = request.GET.get("vista")
    if vista not in VISTAS_BANDEJA:
        vista = "pendientes"
    consultas = _consultas_bandeja(request.user)
    return render(request, "proyectos/bandeja.html", {
        "vista": vista,
        "proyectos": consultas[vista],
        "totales": {nombre: consulta.count() for nombre, consulta in consultas.items()},
    })


@rol_requerido(Rol.PROFESOR, Rol.ADMIN)
@require_POST
def tomar(request, slug):
    """El docente toma un proyecto enviado: pasa a En revisión y queda a su nombre."""
    proyecto = get_object_or_404(Proyecto, slug=slug)
    try:
        cambiar_estado(proyecto, Estado.EN_REVISION, request.user)
    except TransicionNoPermitida:
        messages.warning(request, _("Otro docente ya tomó este proyecto o cambió de estado."))
        return redirect("proyectos:bandeja")
    messages.success(request, _("Tomaste el proyecto. Ahora está en revisión a tu nombre."))
    return redirect("proyectos:revisar", slug=proyecto.slug)


MENSAJES_DECISION = {
    # gettext_lazy: este diccionario se crea al importar el módulo, antes de saber el idioma
    Estado.APROBADO: gettext_lazy("Proyecto aprobado. Ya aparece en la vitrina con el código %(codigo)s."),
    Estado.CON_OBSERVACIONES: gettext_lazy("Pediste cambios. Los autores pueden corregir y reenviar."),
    Estado.RECHAZADO: gettext_lazy("Proyecto rechazado."),
}


@rol_requerido(Rol.PROFESOR, Rol.ADMIN)
def revisar(request, slug):
    """Ficha de revisión: datos del proyecto, historial y formulario de decisión."""
    proyecto = get_object_or_404(Proyecto.objects.con_relaciones().select_related("revisor"), slug=slug)
    if proyecto.estado == Estado.BORRADOR:
        raise Http404  # un borrador todavía no es asunto de los docentes
    puede_decidir = puede_cambiar(request.user, proyecto, Estado.APROBADO)
    form = FormularioDecision(request.POST or None)

    if request.method == "POST":
        if not puede_decidir:
            raise PermissionDenied
        if form.is_valid():
            decision = form.cleaned_data["decision"]
            try:
                evento = cambiar_estado(proyecto, decision, request.user, form.cleaned_data["comentario"])
            except TransicionNoPermitida:
                messages.error(request, _("El proyecto cambió de estado mientras tanto."))
                return redirect("proyectos:revisar", slug=proyecto.slug)
            except ValidationError as error:
                form.add_error("comentario", error)
            else:
                messages.success(request, MENSAJES_DECISION[decision] % {"codigo": proyecto.codigo})
                if not avisar_decision(request, proyecto, evento):
                    messages.warning(request, _("La decisión se guardó, pero no pudimos avisar a los autores por correo."))
                return redirect(reverse("proyectos:bandeja") + "?vista=decididos")

    return render(request, "proyectos/revisar.html", {
        "proyecto": proyecto,
        "autorias": proyecto.autorias.select_related("usuario"),
        "eventos": proyecto.eventos.select_related("actor"),
        "form": form,
        "puede_tomar": puede_cambiar(request.user, proyecto, Estado.EN_REVISION),
        "puede_decidir": puede_decidir,
    })

