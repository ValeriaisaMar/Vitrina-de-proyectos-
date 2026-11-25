"""Vistas de proyectos.

- Estudiantes: listar, crear, editar, eliminar y enviar a revisión.
- Profesores y admins: bandeja, tomar y revisar (módulo 004).
- Admins: periodos académicos (spec 008).

Ninguna vista cambia proyecto.estado directamente: todas llaman a servicios.cambiar_estado().
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from cuentas.decoradores import rol_requerido
from cuentas.models import Rol
from proyectos.correos import avisar_decision, avisar_salida, avisar_transferencia
from proyectos.forms import FormularioDecision, FormularioEnvio, FormularioPeriodo, FormularioProyecto, FormularioTransferir
from proyectos.models import Autoria, Estado, Periodo, Proyecto
from proyectos.permisos import puede_editar, puede_eliminar, puede_salir, puede_transferir
from proyectos.servicios import (
    TransicionNoPermitida,
    cambiar_estado,
    conflicto_de_interes,
    consultas_bandeja,
    puede_cambiar,
)


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
            "puede_salir": puede_salir(request.user, p),
            "transferible": puede_transferir(request.user, p),
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


@login_required
def salir(request, slug):
    """Pide confirmación (GET) y saca (POST) al coautor del proyecto. Se avisa al creador."""
    proyecto = get_object_or_404(Proyecto, slug=slug)
    if not puede_salir(request.user, proyecto):
        raise PermissionDenied
    if request.method == "POST":
        proyecto.autorias.filter(usuario=request.user, es_creador=False).delete()
        avisar_salida(request, proyecto, request.user)
        messages.success(request, _("Saliste del proyecto «%(titulo)s».") % {"titulo": proyecto.titulo})
        return redirect("proyectos:mis_proyectos")
    return render(request, "proyectos/confirmar_salir.html", {"proyecto": proyecto, "creador": proyecto.creador})


@login_required
def transferir(request, slug):
    """El creador le pasa el proyecto a un coautor y sigue en él como coautor."""
    proyecto = get_object_or_404(Proyecto, slug=slug)
    if not puede_transferir(request.user, proyecto):
        raise PermissionDenied
    form = FormularioTransferir(request.POST or None, proyecto=proyecto)
    if request.method == "POST" and form.is_valid():
        nuevo = form.cleaned_data["nuevo_creador"]
        with transaction.atomic():
            # Se bloquean las autorías: si dos peticiones llegan a la vez, la segunda ve el cambio
            autorias = {a.usuario_id: a for a in Autoria.objects.select_for_update().filter(proyecto=proyecto)}
            actual = autorias.get(request.user.pk)
            if actual is None or not actual.es_creador or nuevo.pk not in autorias:
                raise PermissionDenied
            actual.es_creador = False
            actual.save(update_fields=["es_creador"])
            autorias[nuevo.pk].es_creador = True
            autorias[nuevo.pk].save(update_fields=["es_creador"])
        avisar_transferencia(request, proyecto, request.user, nuevo)
        messages.success(request, _("Ahora %(nombre)s es quien creó «%(titulo)s». Tú sigues como coautor.") % {
            "nombre": nuevo.nombre_completo, "titulo": proyecto.titulo,
        })
        return redirect("proyectos:mis_proyectos")
    return render(request, "proyectos/transferir.html", {"form": form, "proyecto": proyecto})


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


@rol_requerido(Rol.PROFESOR, Rol.ADMIN)
def bandeja(request):
    """Bandeja común de revisión: por revisar, en revisión y decididos por mí."""
    vista = request.GET.get("vista")
    if vista not in VISTAS_BANDEJA:
        vista = "pendientes"
    consultas = consultas_bandeja(request.user)
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
        # Conflicto de interés (spec 008): se explica por qué no aparecen los botones
        "es_su_proyecto": conflicto_de_interes(request.user, proyecto),
        "autorias": proyecto.autorias.select_related("usuario"),
        "eventos": proyecto.eventos.select_related("actor"),
        "form": form,
        "puede_tomar": puede_cambiar(request.user, proyecto, Estado.EN_REVISION),
        "puede_decidir": puede_decidir,
    })



# --------------------------------------------------------------------------- Periodos (admins, spec 008)


@rol_requerido(Rol.ADMIN)
def periodos(request):
    """Lista de periodos académicos con su número de proyectos."""
    lista = Periodo.objects.annotate(total_proyectos=Count("proyectos"))
    return render(request, "proyectos/periodos.html", {"periodos": lista})


@rol_requerido(Rol.ADMIN)
def periodo_formulario(request, pk=None):
    """Crea (sin pk) o edita (con pk) un periodo."""
    periodo = get_object_or_404(Periodo, pk=pk) if pk else None
    form = FormularioPeriodo(request.POST or None, instance=periodo)
    if request.method == "POST" and form.is_valid():
        periodo = form.save()
        messages.success(request, _("Guardamos el periodo «%(nombre)s».") % {"nombre": periodo.nombre})
        return redirect("proyectos:periodos")
    return render(request, "proyectos/periodo_formulario.html", {"form": form, "periodo": periodo})


@rol_requerido(Rol.ADMIN)
@require_POST
def periodo_abrir_cerrar(request, pk):
    """Abre o cierra un periodo para entregas."""
    periodo = get_object_or_404(Periodo, pk=pk)
    periodo.abierto = not periodo.abierto
    periodo.save(update_fields=["abierto"])
    if periodo.abierto:
        messages.success(request, _("El periodo «%(nombre)s» está abierto para entregas.") % {"nombre": periodo.nombre})
    else:
        messages.success(request, _("El periodo «%(nombre)s» quedó cerrado.") % {"nombre": periodo.nombre})
    return redirect("proyectos:periodos")


@rol_requerido(Rol.ADMIN)
@require_POST
def periodo_eliminar(request, pk):
    """Borra un periodo sin proyectos. Si tiene proyectos no se puede: se ofrece cerrarlo."""
    periodo = get_object_or_404(Periodo, pk=pk)
    if periodo.proyectos.exists():
        messages.error(request, _("No se puede borrar «%(nombre)s» porque tiene proyectos. Ciérralo para que no reciba más.") % {"nombre": periodo.nombre})
    else:
        periodo.delete()
        messages.success(request, _("Borramos el periodo «%(nombre)s».") % {"nombre": periodo.nombre})
    return redirect("proyectos:periodos")
