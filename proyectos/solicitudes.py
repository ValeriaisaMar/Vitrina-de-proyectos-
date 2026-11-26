"""Elección del profesor revisor (spec 009, historia 5).

Flujo:
1. El creador envía el proyecto y elige un profesor → solicitar(): queda una solicitud pendiente
   (subestado "Esperando aceptación").
2. El profesor acepta → aceptar(): queda como revisor y el proyecto pasa a En revisión.
   O no acepta → no_aceptar(): con mensaje y recomendación opcionales; el proyecto vuelve a
   "Por asignar revisor" y el creador elige de nuevo.
3. Si el profesor no responde en DIAS_PARA_RETIRAR días, el creador puede retirar la solicitud.
4. El admin puede reasignar el revisor de cualquier proyecto enviado o en revisión.

Todo queda en el historial (servicios.registrar_evento) y los cambios de estado pasan, como
siempre, por servicios.cambiar_estado. Las vistas mandan los correos después (proyectos/correos.py).
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from cuentas.models import Perfil, Rol, Usuario
from proyectos.models import (
    DIAS_PARA_RETIRAR,
    ESTADOS_DE_DECISION,
    AccionEvento,
    Estado,
    EstadoSolicitud,
    Proyecto,
    SolicitudRevision,
)
from proyectos.servicios import cambiar_estado, registrar_evento

TOPE_MISMA_ASIGNATURA = 3  # cuántos proyectos aprobados de la asignatura suman puntos (+2 cada uno)


# --------------------------------------------------------------------------- Quién puede revisar


def _contar(consulta, campo):
    """Subconsulta que cuenta filas de `consulta` por profesor, para anotar sin multiplicar filas."""
    return Coalesce(
        Subquery(consulta.filter(**{campo: OuterRef("pk")}).order_by().values(campo).annotate(n=Count("pk")).values("n")[:1],
                 output_field=IntegerField()),
        Value(0),
    )


def profesores(excluir_autores_de=None):
    """Cuentas activas con el rol profesor, con los datos que muestran sus tarjetas.

    Anota sin multiplicar filas (subconsultas): pendientes (solicitudes pendientes + proyectos
    asignados sin decidir) y revisados (proyectos que decidió). Trae perfil y asignaturas.
    """
    consulta = Usuario.objects.filter(is_active=True, roles_asignados__rol=Rol.PROFESOR)
    if excluir_autores_de is not None:
        consulta = consulta.exclude(autorias__proyecto=excluir_autores_de)  # conflicto de interés
    solicitudes = SolicitudRevision.objects.filter(estado=EstadoSolicitud.PENDIENTE)
    asignados = Proyecto.objects.filter(estado__in=[Estado.ENVIADO, Estado.EN_REVISION])
    decididos = Proyecto.objects.filter(estado__in=ESTADOS_DE_DECISION)
    return (
        consulta.distinct()
        .annotate(
            solicitudes_pendientes=_contar(solicitudes, "profesor"),
            asignados=_contar(asignados, "revisor"),
            revisados=_contar(decididos, "revisor"),
        )
        .select_related("perfil")
        .prefetch_related("perfil__asignaturas_imparte", "roles_asignados")
        .order_by("apellidos", "nombres")
    )


def rechazaron(proyecto):
    """Ids de los profesores que ya no aceptaron este proyecto."""
    return set(proyecto.solicitudes.filter(estado=EstadoSolicitud.NO_ACEPTADA).values_list("profesor_id", flat=True))


def es_elegible(profesor, proyecto, para_admin=False):
    """True si se le puede pedir la revisión: profesor activo, no autor y (salvo el admin) disponible."""
    if not profesor.is_active or not profesor.tiene_rol(Rol.PROFESOR) or proyecto.es_autor(profesor):
        return False
    perfil = getattr(profesor, "perfil", None)
    return para_admin or perfil is None or perfil.recibiendo_proyectos


# --------------------------------------------------------------------------- Sugerencias


def sugerir_profesores(proyecto, limite=5):
    """Hasta `limite` profesores sugeridos para revisar el proyecto, cada uno con sus motivos.

    Puntaje (transparente: cada punto tiene su motivo):
      +3 si imparte la asignatura del proyecto.
      +2 por cada proyecto aprobado de esa asignatura que revisó (hasta TOPE_MISMA_ASIGNATURA).
      +1 si revisó proyectos del mismo semestre (de otras asignaturas).
      +1 por cada aptitud suya que coincida con una tecnología del proyecto.
    Desempate: menos pendientes y luego el nombre. Nunca aparecen autores, profesores que no
    están recibiendo proyectos ni quienes ya no aceptaron este proyecto. Solo se sugieren
    profesores con algún punto. Devuelve [{"profesor", "puntaje", "motivos"}].
    """
    candidatos = [
        p for p in profesores(excluir_autores_de=proyecto)
        if p.pk not in rechazaron(proyecto) and p.perfil.recibiendo_proyectos
    ]
    if not candidatos:
        return []
    ids = [p.pk for p in candidatos]
    asignatura = proyecto.asignatura

    imparten = set(Perfil.asignaturas_imparte.through.objects.filter(
        asignatura_id=proyecto.asignatura_id, perfil__usuario_id__in=ids,
    ).values_list("perfil__usuario_id", flat=True))
    misma_asignatura = dict(
        Proyecto.objects.filter(estado=Estado.APROBADO, asignatura=asignatura, revisor_id__in=ids)
        .values("revisor_id").annotate(n=Count("pk")).values_list("revisor_id", "n")
    )
    mismo_semestre = set(
        Proyecto.objects.filter(estado__in=ESTADOS_DE_DECISION, asignatura__semestre=asignatura.semestre, revisor_id__in=ids)
        .exclude(asignatura=asignatura).values_list("revisor_id", flat=True)
    )
    tecnologias = {t.casefold(): t for t in proyecto.tecnologias.values_list("nombre", flat=True)}
    aptitudes = {}
    for usuario_id, nombre in Perfil.aptitudes.through.objects.filter(perfil__usuario_id__in=ids).values_list(
        "perfil__usuario_id", "aptitud__nombre"
    ):
        if nombre.casefold() in tecnologias:
            aptitudes.setdefault(usuario_id, []).append(tecnologias[nombre.casefold()])

    sugerencias = []
    for profesor in candidatos:
        puntaje, motivos = 0, []
        if profesor.pk in imparten:
            puntaje += 3
            motivos.append(_("Imparte %(asignatura)s") % {"asignatura": asignatura.nombre})
        revisados = misma_asignatura.get(profesor.pk, 0)
        if revisados:
            puntaje += 2 * min(revisados, TOPE_MISMA_ASIGNATURA)
            motivos.append(ngettext(
                "Ha revisado %(n)s proyecto de esta asignatura", "Ha revisado %(n)s proyectos de esta asignatura", revisados,
            ) % {"n": revisados})
        if profesor.pk in mismo_semestre:
            puntaje += 1
            motivos.append(_("Ha revisado proyectos del mismo semestre"))
        coinciden = sorted(aptitudes.get(profesor.pk, []))
        if coinciden:
            puntaje += len(coinciden)
            motivos.append(_("Conoce %(tecnologias)s") % {"tecnologias": ", ".join(coinciden)})
        if puntaje:
            sugerencias.append({"profesor": profesor, "puntaje": puntaje, "motivos": motivos})

    sugerencias.sort(key=lambda s: (-s["puntaje"], s["profesor"].solicitudes_pendientes + s["profesor"].asignados,
                                    s["profesor"].nombre_completo.casefold()))
    return sugerencias[:limite]


def recomendacion_vigente(proyecto):
    """El profesor que recomendó quien no aceptó por última vez, si todavía se puede elegir."""
    ultima = proyecto.solicitudes.filter(estado=EstadoSolicitud.NO_ACEPTADA).select_related("profesor_recomendado__perfil").first()
    recomendado = ultima.profesor_recomendado if ultima else None
    if recomendado and es_elegible(recomendado, proyecto) and recomendado.pk not in rechazaron(proyecto):
        # Con las mismas anotaciones que las demás tarjetas (pendientes, revisados…)
        anotado = profesores(excluir_autores_de=proyecto).filter(pk=recomendado.pk).first()
        return {"profesor": anotado or recomendado, "por": ultima.profesor, "mensaje": ultima.mensaje}
    return None


# --------------------------------------------------------------------------- Acciones


def puede_elegir_revisor(usuario, proyecto):
    """Solo el creador, como estudiante, y solo si el proyecto espera revisor."""
    return (
        usuario.is_authenticated and usuario.rol_activo == Rol.ESTUDIANTE
        and proyecto.estado == Estado.ENVIADO and proyecto.subestado == "por_asignar"
        and proyecto.autorias.filter(usuario=usuario, es_creador=True).exists()
    )


def solicitar(proyecto, profesor, actor):
    """El creador pide la revisión a un profesor. Devuelve la SolicitudRevision.

    Lanza PermissionDenied si no es el creador o el proyecto no espera revisor, y ValidationError
    si el profesor no se puede elegir (no está recibiendo proyectos, es autor…). Un profesor que
    ya no aceptó este proyecto sí se puede volver a elegir.
    """
    with transaction.atomic():
        proyecto = Proyecto.objects.select_for_update().get(pk=proyecto.pk)
        if not puede_elegir_revisor(actor, proyecto):
            raise PermissionDenied
        if not es_elegible(profesor, proyecto):
            raise ValidationError(_("No puedes elegir a este profesor."), code="profesor_no_elegible")
        solicitud = SolicitudRevision.objects.create(proyecto=proyecto, profesor=profesor, creada_por=actor)
        registrar_evento(proyecto, actor, AccionEvento.SOLICITUD, profesor=profesor)
    return solicitud


def enviar(proyecto, actor, comentario="", profesor=None):
    """Envía o reenvía el proyecto y, si viene un profesor (primer envío del creador), se lo pide.

    Reenvío con observaciones: el proyecto conserva su revisor y vuelve a él sin elegir.
    Devuelve la solicitud creada o None.
    """
    with transaction.atomic():
        es_reenvio = proyecto.estado == Estado.CON_OBSERVACIONES
        cambiar_estado(proyecto, Estado.ENVIADO, actor, comentario)
        if es_reenvio or profesor is None:
            return None
        return solicitar(proyecto, profesor, actor)


def aceptar(solicitud, profesor):
    """El profesor acepta: queda como revisor y el proyecto pasa a En revisión."""
    with transaction.atomic():
        solicitud = SolicitudRevision.objects.select_for_update().select_related("proyecto").get(pk=solicitud.pk)
        if solicitud.profesor_id != profesor.pk or profesor.rol_activo != Rol.PROFESOR:
            raise PermissionDenied
        if solicitud.estado != EstadoSolicitud.PENDIENTE:
            raise ValidationError(_("Esta solicitud ya no está pendiente."), code="no_pendiente")
        proyecto = solicitud.proyecto
        Proyecto.objects.filter(pk=proyecto.pk).update(revisor=profesor)
        proyecto.revisor = profesor
        solicitud.estado = EstadoSolicitud.ACEPTADA
        solicitud.respondida_en = timezone.now()
        solicitud.save(update_fields=["estado", "respondida_en"])
        cambiar_estado(proyecto, Estado.EN_REVISION, profesor, accion=AccionEvento.ACEPTADA)
    return proyecto


def no_aceptar(solicitud, profesor, mensaje="", recomendado=None):
    """El profesor no acepta, con un mensaje y la recomendación de otro profesor (opcionales)."""
    with transaction.atomic():
        solicitud = SolicitudRevision.objects.select_for_update().select_related("proyecto").get(pk=solicitud.pk)
        if solicitud.profesor_id != profesor.pk or profesor.rol_activo != Rol.PROFESOR:
            raise PermissionDenied
        if solicitud.estado != EstadoSolicitud.PENDIENTE:
            raise ValidationError(_("Esta solicitud ya no está pendiente."), code="no_pendiente")
        if recomendado is not None and (recomendado.pk == profesor.pk or not es_elegible(recomendado, solicitud.proyecto)):
            raise ValidationError(_("No puedes recomendar a ese profesor."), code="recomendado_no_elegible")
        solicitud.estado = EstadoSolicitud.NO_ACEPTADA
        solicitud.mensaje = (mensaje or "").strip()
        solicitud.profesor_recomendado = recomendado
        solicitud.respondida_en = timezone.now()
        solicitud.save(update_fields=["estado", "mensaje", "profesor_recomendado", "respondida_en"])
        registrar_evento(solicitud.proyecto, profesor, AccionEvento.NO_ACEPTADA, solicitud.mensaje, profesor=recomendado)
    return solicitud


def puede_retirar(usuario, solicitud, ahora=None):
    """El creador retira una solicitud pendiente si el profesor no respondió en DIAS_PARA_RETIRAR días.

    Si el profesor ya no puede revisar (perdió el rol o se desactivó su cuenta), se puede retirar
    enseguida: si no, el proyecto quedaría esperando a alguien que no va a responder.
    """
    ahora = ahora or timezone.now()
    proyecto = solicitud.proyecto
    if solicitud.estado != EstadoSolicitud.PENDIENTE or not usuario.is_authenticated or usuario.rol_activo != Rol.ESTUDIANTE:
        return False
    if not proyecto.autorias.filter(usuario=usuario, es_creador=True).exists():
        return False
    profesor_sigue = solicitud.profesor.is_active and solicitud.profesor.tiene_rol(Rol.PROFESOR)
    return not profesor_sigue or ahora >= solicitud.se_puede_retirar_desde


def retirar(solicitud, actor):
    """El creador retira la solicitud; el proyecto vuelve a "Por asignar revisor"."""
    with transaction.atomic():
        solicitud = SolicitudRevision.objects.select_for_update().select_related("proyecto", "profesor").get(pk=solicitud.pk)
        if not puede_retirar(actor, solicitud):
            raise PermissionDenied
        solicitud.estado = EstadoSolicitud.RETIRADA
        solicitud.respondida_en = timezone.now()
        solicitud.save(update_fields=["estado", "respondida_en"])
        registrar_evento(solicitud.proyecto, actor, AccionEvento.RETIRADA, profesor=solicitud.profesor)
    return solicitud


def reasignar(proyecto, nuevo, admin, motivo=""):
    """El admin asigna otro revisor a un proyecto enviado o en revisión. Queda en el historial.

    La solicitud pendiente (si había) queda como "reasignada" y se registra una aceptada a nombre
    del nuevo profesor. En revisión sigue en revisión; Enviado queda "Por revisar" con el nuevo.
    """
    with transaction.atomic():
        proyecto = Proyecto.objects.select_for_update().get(pk=proyecto.pk)
        if admin.rol_activo != Rol.ADMIN or proyecto.es_autor(admin):
            raise PermissionDenied
        if proyecto.estado not in (Estado.ENVIADO, Estado.EN_REVISION):
            raise ValidationError(_("Solo se reasignan proyectos enviados o en revisión."), code="estado")
        if not es_elegible(nuevo, proyecto, para_admin=True):
            raise ValidationError(_("Ese profesor no puede revisar este proyecto."), code="profesor_no_elegible")
        ahora = timezone.now()
        proyecto.solicitudes.filter(estado=EstadoSolicitud.PENDIENTE).update(estado=EstadoSolicitud.REASIGNADA, respondida_en=ahora)
        SolicitudRevision.objects.create(proyecto=proyecto, profesor=nuevo, estado=EstadoSolicitud.ACEPTADA,
                                         creada_por=admin, respondida_en=ahora, mensaje=(motivo or "").strip())
        proyecto.revisor = nuevo
        proyecto.save(update_fields=["revisor", "actualizado_en"])
        registrar_evento(proyecto, admin, AccionEvento.REASIGNADA, motivo, profesor=nuevo)
    return proyecto


def solicitudes_para(profesor):
    """Solicitudes pendientes de un profesor, de la más antigua a la más nueva."""
    return (
        SolicitudRevision.objects.filter(profesor=profesor, estado=EstadoSolicitud.PENDIENTE)
        .select_related("proyecto__asignatura", "creada_por")
        .prefetch_related("proyecto__autores", "proyecto__tecnologias")
        .order_by("creada_en")
    )


def recordatorios_pendientes(ahora=None, dias=3):
    """Solicitudes pendientes con `dias` o más días y sin recordatorio (para el comando opcional)."""
    from datetime import timedelta

    ahora = ahora or timezone.now()
    return SolicitudRevision.objects.filter(
        estado=EstadoSolicitud.PENDIENTE, recordatorio_enviado=False, creada_en__lte=ahora - timedelta(days=dias),
    ).select_related("proyecto", "profesor")

