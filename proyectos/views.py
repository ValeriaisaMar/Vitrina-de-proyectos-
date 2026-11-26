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
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from cuentas.decoradores import rol_requerido
from cuentas.models import Rol
from proyectos import solicitudes
from proyectos.correos import (
    avisar_aceptada,
    avisar_decision,
    avisar_no_aceptada,
    avisar_reasignada,
    avisar_retirada,
    avisar_salida,
    avisar_solicitud,
    avisar_transferencia,
    base_url,
)
from proyectos.forms import (
    FormularioAsignatura,
    FormularioDecision,
    FormularioElegirProfesor,
    FormularioEnvio,
    FormularioNoAceptar,
    FormularioPeriodo,
    FormularioPlan,
    FormularioProyecto,
    FormularioReasignar,
    FormularioTransferir,
)
from proyectos.models import Asignatura, Autoria, Estado, EstadoSolicitud, Periodo, PlanEstudio, Proyecto, SolicitudRevision
from proyectos.permisos import puede_editar, puede_eliminar, puede_salir, puede_transferir
from proyectos.servicios import (
    TransicionNoPermitida,
    cambiar_estado,
    conflicto_de_interes,
    marcar_actual,
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
    """Pide confirmación (GET) y envía (POST) un proyecto a revisión. También sirve para reenviar.

    Spec 009: en el primer envío, el creador elige aquí al profesor que lo revisará. Un coautor
    puede enviar, pero sin elegir: el proyecto queda "Por asignar revisor" y elige el creador.
    Al reenviar con observaciones vuelve al mismo profesor, sin elegir.
    """
    proyecto = get_object_or_404(Proyecto.objects.select_related("asignatura"), slug=slug)
    if not puede_cambiar(request.user, proyecto, Estado.ENVIADO):
        raise PermissionDenied
    reenvio = proyecto.estado == Estado.CON_OBSERVACIONES
    es_creador = proyecto.autorias.filter(usuario=request.user, es_creador=True).exists()
    elige = es_creador and not reenvio
    # Spec 009: el primer envío toma el período actual; sin período actual no se puede enviar
    periodo_actual = Periodo.actual()
    sin_periodo = not reenvio and periodo_actual is None

    form = FormularioEnvio(request.POST or None)
    eleccion = FormularioElegirProfesor(request.POST or None, elegibles=_elegibles(proyecto)) if elige else None
    if request.method == "POST" and form.is_valid() and (eleccion is None or eleccion.is_valid()):
        profesor = eleccion.cleaned_data["profesor"] if eleccion else None
        try:
            solicitud = solicitudes.enviar(proyecto, request.user, form.cleaned_data["comentario"], profesor)
        except TransicionNoPermitida:
            messages.error(request, _("El proyecto cambió de estado mientras tanto. Revisa cómo quedó."))
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return redirect("proyectos:enviar", slug=proyecto.slug)
        else:
            if solicitud:
                avisar_solicitud(base_url(request), solicitud)
                messages.success(request, _("Enviamos tu proyecto y le pedimos a %(profesor)s que lo revise. Te avisaremos cuando responda.") % {"profesor": profesor.nombre_completo})
            elif reenvio:
                messages.success(request, _("Reenviamos tu proyecto al mismo profesor. Te avisaremos por correo cuando decida."))
            else:
                messages.success(request, _("Enviamos tu proyecto. Quien lo creó debe elegir al profesor que lo revisará."))
        return redirect(proyecto.get_absolute_url())
    return render(request, "proyectos/enviar.html", {
        "form": form,
        "eleccion": eleccion,
        "proyecto": proyecto,
        "reenvio": reenvio,
        "observacion": proyecto.ultima_decision if reenvio else None,
        "periodo_envio": periodo_actual,
        "sin_periodo": sin_periodo,
        **(_contexto_eleccion(request, proyecto) if elige else {}),
    })


# --------------------------------------------------------------------------- Elegir revisor (spec 009)

ORDENES_PROFESORES = ("relevancia", "nombre", "pendientes")


def _elegibles(proyecto):
    """Profesores que se pueden elegir: activos, no autores y recibiendo proyectos."""
    return solicitudes.profesores(excluir_autores_de=proyecto).filter(perfil__recibiendo_proyectos=True)


def _contexto_eleccion(request, proyecto):
    """Sugerencias, recomendación y la lista completa de profesores (con filtros) para elegir revisor.

    Los filtros llegan por GET (?q=, ?asignatura=, ?semestre=, ?disponibles=1, ?orden=) y también
    funcionan sin JavaScript; con JavaScript, static/js/revisor.js filtra al instante.
    """
    datos = request.GET
    rechazos = solicitudes.rechazaron(proyecto)
    todos = []
    for profesor in solicitudes.profesores(excluir_autores_de=proyecto):
        asignaturas = list(profesor.perfil.asignaturas_imparte.all())
        profesor.asignaturas = asignaturas
        profesor.imparte_la_asignatura = any(a.pk == proyecto.asignatura_id for a in asignaturas)
        profesor.disponible = profesor.perfil.recibiendo_proyectos
        profesor.ya_rechazo = profesor.pk in rechazos
        profesor.pendientes = profesor.solicitudes_pendientes + profesor.asignados
        todos.append(profesor)

    texto = " ".join(datos.get("q", "").split()).casefold()
    if texto:
        todos = [p for p in todos if texto in p.nombre_completo.casefold()]
    if datos.get("asignatura", "").isdigit():
        todos = [p for p in todos if any(a.pk == int(datos["asignatura"]) for a in p.asignaturas)]
    if datos.get("semestre", "").isdigit():
        todos = [p for p in todos if any(a.semestre == int(datos["semestre"]) for a in p.asignaturas)]
    if datos.get("disponibles"):
        todos = [p for p in todos if p.disponible]
    orden = datos.get("orden") if datos.get("orden") in ORDENES_PROFESORES else "relevancia"
    if orden == "nombre":
        todos.sort(key=lambda p: p.nombre_completo.casefold())
    elif orden == "pendientes":
        todos.sort(key=lambda p: (p.pendientes, p.nombre_completo.casefold()))
    else:  # primero quienes imparten la asignatura del proyecto, luego el resto por nombre
        todos.sort(key=lambda p: (not p.imparte_la_asignatura, p.nombre_completo.casefold()))

    from proyectos.forms import asignaturas_elegibles, opciones_por_plan_y_semestre

    return {
        "sugerencias": solicitudes.sugerir_profesores(proyecto),
        "recomendacion": solicitudes.recomendacion_vigente(proyecto),
        "todos": todos,
        "filtrando": any(datos.get(c) for c in ("q", "asignatura", "semestre", "disponibles", "orden")),
        "filtros": {"q": datos.get("q", ""), "asignatura": datos.get("asignatura", ""), "semestre": datos.get("semestre", ""),
                    "disponibles": bool(datos.get("disponibles")), "orden": orden},
        "opciones_asignatura": opciones_por_plan_y_semestre(asignaturas_elegibles(), vacio=False),
        "semestres": range(1, 11),
        "elegido": request.POST.get("profesor") or request.GET.get("profesor", ""),
    }


@login_required
def elegir_revisor(request, slug):
    """El creador elige (o vuelve a elegir) al profesor de un proyecto "Por asignar revisor"."""
    proyecto = get_object_or_404(Proyecto.objects.select_related("asignatura"), slug=slug)
    if not solicitudes.puede_elegir_revisor(request.user, proyecto):
        raise PermissionDenied
    eleccion = FormularioElegirProfesor(request.POST or None, elegibles=_elegibles(proyecto))
    if request.method == "POST" and eleccion.is_valid():
        profesor = eleccion.cleaned_data["profesor"]
        try:
            solicitud = solicitudes.solicitar(proyecto, profesor, request.user)
        except ValidationError as error:
            messages.error(request, error.messages[0])
        else:
            avisar_solicitud(base_url(request), solicitud)
            messages.success(request, _("Le pedimos a %(profesor)s que revise tu proyecto. Te avisaremos cuando responda.") % {"profesor": profesor.nombre_completo})
            return redirect(proyecto.get_absolute_url())
    return render(request, "proyectos/elegir_revisor.html", {
        "proyecto": proyecto, "eleccion": eleccion, **_contexto_eleccion(request, proyecto),
    })


@login_required
@require_POST
def retirar_solicitud(request, slug):
    """El creador retira la solicitud que el profesor no respondió en 5 días y vuelve a elegir."""
    proyecto = get_object_or_404(Proyecto, slug=slug)
    solicitud = proyecto.solicitud_pendiente
    if solicitud is None or not solicitudes.puede_retirar(request.user, solicitud):
        raise PermissionDenied
    solicitudes.retirar(solicitud, request.user)
    avisar_retirada(base_url(request), solicitud)
    messages.success(request, _("Retiraste la solicitud. Elige a otro profesor."))
    return redirect("proyectos:elegir_revisor", slug=proyecto.slug)


@rol_requerido(Rol.PROFESOR)
def lista_solicitudes(request):
    """"Solicitudes de revisión": lo que los estudiantes le pidieron a este profesor."""
    return render(request, "proyectos/solicitudes.html", {"solicitudes": solicitudes.solicitudes_para(request.user)})


@rol_requerido(Rol.PROFESOR)
@require_POST
def aceptar_solicitud(request, pk):
    """El profesor acepta revisar: el proyecto pasa a En revisión a su nombre."""
    solicitud = get_object_or_404(SolicitudRevision, pk=pk, profesor=request.user)
    try:
        proyecto = solicitudes.aceptar(solicitud, request.user)
    except (ValidationError, TransicionNoPermitida):
        messages.warning(request, _("Esta solicitud ya no está pendiente."))
        return redirect("proyectos:solicitudes")
    avisar_aceptada(base_url(request), proyecto, request.user)
    messages.success(request, _("Aceptaste revisar «%(titulo)s». Ya está en tu bandeja.") % {"titulo": proyecto.titulo})
    return redirect("proyectos:revisar", slug=proyecto.slug)


@rol_requerido(Rol.PROFESOR)
def no_aceptar_solicitud(request, pk):
    """El profesor no acepta: puede dejar un mensaje y recomendar a otro profesor."""
    solicitud = get_object_or_404(SolicitudRevision.objects.select_related("proyecto"), pk=pk, profesor=request.user)
    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        messages.warning(request, _("Esta solicitud ya no está pendiente."))
        return redirect("proyectos:solicitudes")
    elegibles = _elegibles(solicitud.proyecto).exclude(pk=request.user.pk)
    form = FormularioNoAceptar(request.POST or None, elegibles=elegibles)
    if request.method == "POST" and form.is_valid():
        try:
            solicitud = solicitudes.no_aceptar(solicitud, request.user, form.cleaned_data["mensaje"], form.cleaned_data["recomendado"])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            avisar_no_aceptada(base_url(request), solicitud)
            messages.success(request, _("Avisamos a los estudiantes que no puedes revisar «%(titulo)s».") % {"titulo": solicitud.proyecto.titulo})
            return redirect("proyectos:solicitudes")
    return render(request, "proyectos/no_aceptar.html", {"solicitud": solicitud, "form": form})


@rol_requerido(Rol.ADMIN)
def reasignar(request, slug):
    """El admin asigna otro profesor revisor a un proyecto enviado o en revisión (queda en el historial)."""
    proyecto = get_object_or_404(Proyecto.objects.select_related("revisor"), slug=slug)
    if proyecto.estado not in (Estado.ENVIADO, Estado.EN_REVISION):
        raise Http404
    elegibles = solicitudes.profesores(excluir_autores_de=proyecto)
    if proyecto.revisor_id:
        elegibles = elegibles.exclude(pk=proyecto.revisor_id)
    form = FormularioReasignar(request.POST or None, elegibles=elegibles)
    if request.method == "POST" and form.is_valid():
        nuevo = form.cleaned_data["profesor"]
        try:
            solicitudes.reasignar(proyecto, nuevo, request.user, form.cleaned_data["motivo"])
        except ValidationError as error:
            form.add_error("profesor", error)
        else:
            avisar_reasignada(base_url(request), proyecto, nuevo)
            messages.success(request, _("Ahora %(profesor)s revisa «%(titulo)s».") % {"profesor": nuevo.nombre_completo, "titulo": proyecto.titulo})
            return redirect("proyectos:bandeja")
    return render(request, "proyectos/reasignar.html", {"proyecto": proyecto, "form": form, "pendiente": proyecto.solicitud_pendiente})


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


@rol_requerido(Rol.PROFESOR)
@require_POST
def tomar(request, slug):
    """El profesor asignado empieza a revisar un proyecto "Por revisar" (reenviado o reasignado).

    Spec 009: ya nadie "toma" proyectos de una bandeja común; solo el revisor asignado puede.
    """
    proyecto = get_object_or_404(Proyecto, slug=slug)
    try:
        cambiar_estado(proyecto, Estado.EN_REVISION, request.user)
    except TransicionNoPermitida:
        messages.warning(request, _("El proyecto cambió de estado mientras tanto."))
        return redirect("proyectos:bandeja")
    messages.success(request, _("Empezaste la revisión. El proyecto está en revisión a tu nombre."))
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
        "eventos": proyecto.eventos.select_related("actor", "profesor"),
        "form": form,
        "puede_tomar": puede_cambiar(request.user, proyecto, Estado.EN_REVISION),
        "puede_decidir": puede_decidir,
        "puede_reasignar": request.user.es_admin and proyecto.estado in (Estado.ENVIADO, Estado.EN_REVISION),
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
def periodo_marcar_actual(request, pk):
    """Pide confirmación (GET) y marca (POST) el período como el actual (spec 009).

    Solo puede haber un período actual: marcar otro desmarca el anterior.
    """
    periodo = get_object_or_404(Periodo, pk=pk)
    anterior = Periodo.objects.filter(es_actual=True).exclude(pk=periodo.pk).first()
    if request.method == "POST":
        marcar_actual(periodo)
        messages.success(request, _("«%(nombre)s» es ahora el período académico actual.") % {"nombre": periodo.nombre})
        return redirect("proyectos:periodos")
    return render(request, "proyectos/periodo_confirmar_actual.html", {"periodo": periodo, "anterior": anterior})


@rol_requerido(Rol.ADMIN)
@require_POST
def periodo_eliminar(request, pk):
    """Borra un periodo sin proyectos que no sea el actual."""
    periodo = get_object_or_404(Periodo, pk=pk)
    if periodo.es_actual:
        messages.error(request, _("No se puede borrar «%(nombre)s» porque es el período actual. Marca otro como actual primero.") % {"nombre": periodo.nombre})
    elif periodo.proyectos.exists() or periodo.proyectos_aprobados.exists():
        messages.error(request, _("No se puede borrar «%(nombre)s» porque tiene proyectos.") % {"nombre": periodo.nombre})
    else:
        periodo.delete()
        messages.success(request, _("Borramos el periodo «%(nombre)s».") % {"nombre": periodo.nombre})
    return redirect("proyectos:periodos")


# --------------------------------------------------------------------------- Plan de estudios (admins, spec 009)


@rol_requerido(Rol.ADMIN)
def planes(request):
    """Planes de estudio con su número de asignaturas (activas y en total)."""
    lista = PlanEstudio.objects.annotate(
        total=Count("asignaturas", distinct=True),
        activas=Count("asignaturas", filter=Q(asignaturas__activa=True), distinct=True),
    )
    return render(request, "proyectos/planes.html", {"planes": lista})


@rol_requerido(Rol.ADMIN)
def plan_formulario(request, pk=None):
    """Crea (sin pk) o edita (con pk) un plan de estudios."""
    plan = get_object_or_404(PlanEstudio, pk=pk) if pk else None
    form = FormularioPlan(request.POST or None, instance=plan)
    if request.method == "POST" and form.is_valid():
        plan = form.save()
        messages.success(request, _("Guardamos el plan «%(nombre)s».") % {"nombre": plan.nombre})
        return redirect("proyectos:plan", pk=plan.pk)
    return render(request, "proyectos/plan_formulario.html", {"form": form, "plan": plan})


@rol_requerido(Rol.ADMIN)
def plan(request, pk):
    """Asignaturas del plan agrupadas por semestre, con cuántos proyectos usa cada una."""
    plan = get_object_or_404(PlanEstudio, pk=pk)
    asignaturas = plan.asignaturas.annotate(total_proyectos=Count("proyectos", distinct=True)).order_by("semestre", "nombre")
    semestres = {}
    for asignatura in asignaturas:
        semestres.setdefault(asignatura.semestre, []).append(asignatura)
    return render(request, "proyectos/plan.html", {"plan": plan, "semestres": sorted(semestres.items())})


@rol_requerido(Rol.ADMIN)
def asignatura_formulario(request, plan_pk=None, pk=None):
    """Crea una asignatura en un plan (plan_pk) o edita una existente (pk)."""
    asignatura = get_object_or_404(Asignatura.objects.select_related("plan"), pk=pk) if pk else None
    plan = asignatura.plan if asignatura else get_object_or_404(PlanEstudio, pk=plan_pk)
    form = FormularioAsignatura(request.POST or None, instance=asignatura, plan=plan)
    if request.method == "POST" and form.is_valid():
        asignatura = form.save()
        messages.success(request, _("Guardamos la asignatura «%(nombre)s».") % {"nombre": asignatura.nombre})
        return redirect("proyectos:plan", pk=plan.pk)
    return render(request, "proyectos/asignatura_formulario.html", {"form": form, "plan": plan, "asignatura": asignatura})


@rol_requerido(Rol.ADMIN)
@require_POST
def plan_activar(request, pk):
    """Activa o desactiva un plan."""
    plan = get_object_or_404(PlanEstudio, pk=pk)
    plan.activo = not plan.activo
    plan.save(update_fields=["activo"])
    if plan.activo:
        messages.success(request, _("El plan «%(nombre)s» está activo.") % {"nombre": plan.nombre})
    else:
        messages.success(request, _("Desactivamos el plan «%(nombre)s»: sus asignaturas ya no se ofrecen en los formularios.") % {"nombre": plan.nombre})
    if request.POST.get("volver") == "plan":
        return redirect("proyectos:plan", pk=plan.pk)
    return redirect("proyectos:planes")


@rol_requerido(Rol.ADMIN)
@require_POST
def asignatura_activar(request, pk):
    """Activa o desactiva una asignatura."""
    asignatura = get_object_or_404(Asignatura, pk=pk)
    asignatura.activa = not asignatura.activa
    asignatura.save(update_fields=["activa"])
    if asignatura.activa:
        messages.success(request, _("La asignatura «%(nombre)s» está activa.") % {"nombre": asignatura.nombre})
    else:
        messages.success(request, _("Desactivamos «%(nombre)s». Quienes ya la tienen la conservan.") % {"nombre": asignatura.nombre})
    return redirect("proyectos:plan", pk=asignatura.plan_id)


@rol_requerido(Rol.ADMIN)
@require_POST
def plan_eliminar(request, pk):
    """Borra un plan sin asignaturas. Si tiene, no se puede: se ofrece desactivarlo."""
    plan = get_object_or_404(PlanEstudio, pk=pk)
    if plan.asignaturas.exists():
        messages.error(request, _("No se puede borrar «%(nombre)s» porque tiene asignaturas. Desactívalo para que no se ofrezca.") % {"nombre": plan.nombre})
        return redirect("proyectos:plan", pk=plan.pk)
    plan.delete()
    messages.success(request, _("Borramos el plan «%(nombre)s».") % {"nombre": plan.nombre})
    return redirect("proyectos:planes")


@rol_requerido(Rol.ADMIN)
@require_POST
def asignatura_eliminar(request, pk):
    """Borra una asignatura que nadie usa. Si está en uso, no se puede: se ofrece desactivarla."""
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if asignatura.en_uso:
        messages.error(request, _("No se puede borrar «%(nombre)s» porque está en uso. Desactívala para que no se ofrezca.") % {"nombre": asignatura.nombre})
    else:
        asignatura.delete()
        messages.success(request, _("Borramos la asignatura «%(nombre)s».") % {"nombre": asignatura.nombre})
    return redirect("proyectos:plan", pk=asignatura.plan_id)
