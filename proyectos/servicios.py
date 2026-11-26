"""Cambios de estado de los proyectos (constitución, principio VII).

Esta es la ÚNICA puerta para cambiar el estado de un proyecto. Las vistas, el admin y cualquier
código futuro llaman a cambiar_estado(); nadie escribe proyecto.estado = ... a mano.

La regla completa vive en la tabla TRANSICIONES: para cada pareja (desde, hacia) dice quién
puede hacer el cambio. Leer la tabla es leer la constitución.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils import timezone
from django.utils.translation import gettext as _

from cuentas.models import Rol
from proyectos.models import ESTADOS_DE_DECISION, AccionEvento, Consecutivo, Estado, EventoEstado, Periodo, Proyecto

# Quién puede hacer cada cambio (siempre según el ROL ACTIVO, spec 008):
#   "autor"   → cualquier autor del proyecto, actuando como estudiante
#   "revisor" → el profesor ASIGNADO al proyecto (proyecto.revisor), actuando como profesor
# Spec 009: el revisor lo elige el creador y el profesor acepta (proyectos/solicitudes.py), o lo
# reasigna el admin. El admin ya no revisa ni decide. Pasar de Enviado a En revisión lo hace el
# profesor asignado: al aceptar la solicitud o al retomar un proyecto reenviado.
# Conflicto de interés: nadie revisa, aprueba ni rechaza un proyecto del que es autor.
AUTOR, REVISOR = "autor", "revisor"

TRANSICIONES = {
    (Estado.BORRADOR, Estado.ENVIADO): AUTOR,
    (Estado.CON_OBSERVACIONES, Estado.ENVIADO): AUTOR,
    (Estado.ENVIADO, Estado.EN_REVISION): REVISOR,
    (Estado.EN_REVISION, Estado.APROBADO): REVISOR,
    (Estado.EN_REVISION, Estado.CON_OBSERVACIONES): REVISOR,
    (Estado.EN_REVISION, Estado.RECHAZADO): REVISOR,
}

REQUIEREN_COMENTARIO = {Estado.CON_OBSERVACIONES, Estado.RECHAZADO}


class TransicionNoPermitida(Exception):
    """El cambio pedido no está en la tabla (por ejemplo, de Borrador a Aprobado)."""


def sin_periodo_actual():
    """El error que se lanza al enviar sin período actual (spec 009). Se traduce al usarlo."""
    return ValidationError(_("No hay un período académico activo. Avísale a la administración."), code="sin_periodo")


def _cumple(usuario, proyecto, quien):
    if not usuario.is_authenticated or not usuario.is_active:
        return False
    rol = usuario.rol_activo
    if quien == AUTOR:
        return rol == Rol.ESTUDIANTE and proyecto.es_autor(usuario)
    if conflicto_de_interes(usuario, proyecto):
        return False
    if quien == REVISOR:
        return rol == Rol.PROFESOR and proyecto.revisor_id == usuario.pk
    return False


def conflicto_de_interes(usuario, proyecto):
    """True si el docente es autor del proyecto: entonces no puede revisarlo ni decidirlo."""
    return proyecto.es_autor(usuario)


def puede_cambiar(usuario, proyecto, nuevo):
    """True si el usuario puede llevar el proyecto, tal como está ahora, al estado nuevo.

    Sirve para mostrar u ocultar botones. La comprobación que vale es la de cambiar_estado().
    """
    quien = TRANSICIONES.get((proyecto.estado, nuevo))
    return quien is not None and _cumple(usuario, proyecto, quien)


def generar_codigo(anio):
    """Devuelve el siguiente código del año, por ejemplo VP-2026-0007.

    La fila del año se bloquea con select_for_update(): si dos aprobaciones llegan a la vez,
    la segunda espera a que termine la primera y nunca reciben el mismo número.
    Debe llamarse dentro de una transacción.
    """
    Consecutivo.objects.get_or_create(anio=anio)
    contador = Consecutivo.objects.select_for_update().get(anio=anio)
    contador.ultimo += 1
    contador.save(update_fields=["ultimo"])
    return f"VP-{anio}-{contador.ultimo:04d}"


def cambiar_estado(proyecto, nuevo, actor, comentario="", accion=AccionEvento.ESTADO):
    """Cambia el estado del proyecto y registra el evento. Devuelve el EventoEstado creado.

    Lanza:
      TransicionNoPermitida: el cambio no está en la tabla (o el proyecto ya cambió).
      PermissionDenied:      el actor no puede hacer este cambio.
      ValidationError:       falta el comentario obligatorio, o se envía sin período actual.

    Período (spec 009): al enviar por primera vez (Borrador → Enviado) el proyecto toma el período
    actual; al aprobar guarda el período actual como período de aprobación.
    """
    comentario = (comentario or "").strip()
    with transaction.atomic():
        # Se vuelve a leer el proyecto bloqueando su fila: si otro profesor lo está tomando en
        # este mismo instante, esperamos y vemos el estado real, no el que teníamos en memoria.
        bloqueado = Proyecto.objects.select_for_update().get(pk=proyecto.pk)
        anterior = bloqueado.estado

        quien = TRANSICIONES.get((anterior, nuevo))
        if quien is None:
            raise TransicionNoPermitida(f"No se puede pasar de {anterior} a {nuevo}.")
        if not _cumple(actor, bloqueado, quien):
            raise PermissionDenied
        if nuevo in REQUIEREN_COMENTARIO and not comentario:
            raise ValidationError(_("Escribe un comentario para explicar la decisión."), code="comentario")

        bloqueado.estado = nuevo
        campos = ["estado", "actualizado_en"]
        # El revisor ya no cambia aquí (spec 009): lo fija la aceptación de la solicitud o el admin.
        # Al reenviar con observaciones se conserva, así el proyecto vuelve al mismo profesor.
        actual = Periodo.objects.filter(es_actual=True).first()  # sin caché: aquí se decide
        if anterior == Estado.BORRADOR and nuevo == Estado.ENVIADO:
            if actual is None:
                raise sin_periodo_actual()
            bloqueado.periodo = actual
            campos.append("periodo")
        if nuevo == Estado.APROBADO:
            bloqueado.aprobado_en = timezone.now()
            bloqueado.codigo = generar_codigo(timezone.localdate().year)
            bloqueado.periodo_aprobacion = actual or bloqueado.periodo
            campos += ["aprobado_en", "codigo", "periodo_aprobacion"]
        bloqueado.save(update_fields=campos)

        evento = EventoEstado.objects.create(
            proyecto=bloqueado, estado_anterior=anterior, estado_nuevo=nuevo,
            actor=actor, comentario=comentario, accion=accion,
        )

    # El objeto que recibió la vista queda al día con lo que se guardó
    for campo in ("estado", "revisor_id", "periodo_id", "periodo_aprobacion_id", "aprobado_en", "codigo", "actualizado_en"):
        setattr(proyecto, campo, getattr(bloqueado, campo))
    return evento


def registrar_evento(proyecto, actor, accion, comentario="", profesor=None):
    """Deja en el historial una acción que no cambia el estado (solicitud, retirada, reasignación…).

    El historial es uno solo (constitución, VII): así la línea de tiempo del proyecto cuenta
    también quién pidió la revisión a quién y qué respondió. El estado queda igual.
    """
    return EventoEstado.objects.create(
        proyecto=proyecto, estado_anterior=proyecto.estado, estado_nuevo=proyecto.estado,
        actor=actor, accion=accion, comentario=(comentario or "").strip(), profesor=profesor,
    )


# --------------------------------------------------------------------------- Período actual (spec 009)


def marcar_actual(periodo):
    """Deja este período como el actual y desmarca el anterior, en una sola transacción.

    Primero se desmarca y después se marca: si se hiciera al revés, por un instante habría dos
    actuales y la restricción única de la base de datos lo rechazaría. Devuelve el anterior (o None).
    """
    with transaction.atomic():
        anterior = Periodo.objects.select_for_update().filter(es_actual=True).exclude(pk=periodo.pk).first()
        if anterior is not None:
            anterior.es_actual = False
            anterior.save(update_fields=["es_actual"])
        periodo.es_actual = True
        periodo.save(update_fields=["es_actual"])
    return anterior


# --------------------------------------------------------------------------- Consultas de la bandeja
# Viven aquí (y no en views.py) porque también las usa el panel de vitrina, y una app solo puede
# importar modelos, formularios o servicios de otra (constitución, principio I).


def consultas_bandeja(usuario):
    """Las tres listas de la bandeja. Cada proyecto trae la fecha que importa en esa lista.

    Spec 009: el profesor ve solo los proyectos que tiene asignados (por revisar, en revisión y los
    que decidió). El admin ve todos los enviados y en revisión, para poder reasignar el revisor.
    Los proyectos de los que el docente es autor no aparecen (conflicto de interés, spec 008).
    """
    base = (
        Proyecto.objects.exclude(autores=usuario).con_subestado()
        .select_related("asignatura", "revisor", "periodo").prefetch_related("autores")
    )
    # Solo cambios reales hacia ese estado: los eventos de solicitudes (spec 009) no cambian el estado
    eventos_a = lambda estado: Q(eventos__estado_nuevo=estado) & ~Q(eventos__estado_anterior=estado)  # noqa: E731
    es_profesor = usuario.rol_activo == Rol.PROFESOR

    pendientes = base.filter(estado=Estado.ENVIADO)
    if es_profesor:
        pendientes = pendientes.filter(revisor=usuario)
    pendientes = (
        pendientes
        .annotate(fecha=Max("eventos__creado_en", filter=eventos_a(Estado.ENVIADO)),
                  envios=Count("eventos", filter=eventos_a(Estado.ENVIADO)))
        .order_by("fecha")  # los que más tiempo llevan esperando, primero
    )

    en_revision = base.filter(estado=Estado.EN_REVISION)
    if es_profesor:
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
