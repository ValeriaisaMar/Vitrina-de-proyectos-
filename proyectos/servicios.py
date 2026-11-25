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
from proyectos.models import ESTADOS_DE_DECISION, Consecutivo, Estado, EventoEstado, Proyecto

# Quién puede hacer cada cambio (siempre según el ROL ACTIVO, spec 008):
#   "autor"   → cualquier autor del proyecto, actuando como estudiante
#   "docente" → cualquier profesor o admin que NO sea autor del proyecto
#   "revisor" → el profesor que tomó el proyecto, o un admin, que NO sea autor del proyecto
# Conflicto de interés: nadie revisa, aprueba ni rechaza un proyecto del que es autor.
AUTOR, DOCENTE, REVISOR = "autor", "docente", "revisor"

TRANSICIONES = {
    (Estado.BORRADOR, Estado.ENVIADO): AUTOR,
    (Estado.CON_OBSERVACIONES, Estado.ENVIADO): AUTOR,
    (Estado.ENVIADO, Estado.EN_REVISION): DOCENTE,
    (Estado.EN_REVISION, Estado.APROBADO): REVISOR,
    (Estado.EN_REVISION, Estado.CON_OBSERVACIONES): REVISOR,
    (Estado.EN_REVISION, Estado.RECHAZADO): REVISOR,
}

REQUIEREN_COMENTARIO = {Estado.CON_OBSERVACIONES, Estado.RECHAZADO}


class TransicionNoPermitida(Exception):
    """El cambio pedido no está en la tabla (por ejemplo, de Borrador a Aprobado)."""


def _cumple(usuario, proyecto, quien):
    if not usuario.is_authenticated or not usuario.is_active:
        return False
    rol = usuario.rol_activo
    if quien == AUTOR:
        return rol == Rol.ESTUDIANTE and proyecto.es_autor(usuario)
    if conflicto_de_interes(usuario, proyecto):
        return False
    if quien == DOCENTE:
        return rol in (Rol.PROFESOR, Rol.ADMIN)
    if quien == REVISOR:
        return rol == Rol.ADMIN or (rol == Rol.PROFESOR and proyecto.revisor_id == usuario.pk)
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


def cambiar_estado(proyecto, nuevo, actor, comentario=""):
    """Cambia el estado del proyecto y registra el evento. Devuelve el EventoEstado creado.

    Lanza:
      TransicionNoPermitida: el cambio no está en la tabla (o el proyecto ya cambió).
      PermissionDenied:      el actor no puede hacer este cambio.
      ValidationError:       falta el comentario obligatorio.
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
        if nuevo == Estado.EN_REVISION or nuevo in ESTADOS_DE_DECISION:
            # Al tomar queda a nombre de quien lo toma; al decidir, de quien decide. Así el
            # certificado y la verificación nombran a quien de verdad aprobó (puede ser un admin).
            bloqueado.revisor = actor
            campos.append("revisor")
        if nuevo == Estado.APROBADO:
            bloqueado.aprobado_en = timezone.now()
            bloqueado.codigo = generar_codigo(timezone.localdate().year)
            campos += ["aprobado_en", "codigo"]
        bloqueado.save(update_fields=campos)

        evento = EventoEstado.objects.create(
            proyecto=bloqueado, estado_anterior=anterior, estado_nuevo=nuevo,
            actor=actor, comentario=comentario,
        )

    # El objeto que recibió la vista queda al día con lo que se guardó
    for campo in ("estado", "revisor_id", "aprobado_en", "codigo", "actualizado_en"):
        setattr(proyecto, campo, getattr(bloqueado, campo))
    return evento


# --------------------------------------------------------------------------- Consultas de la bandeja
# Viven aquí (y no en views.py) porque también las usa el panel de vitrina, y una app solo puede
# importar modelos, formularios o servicios de otra (constitución, principio I).


def consultas_bandeja(usuario):
    """Las tres listas de la bandeja. Cada proyecto trae la fecha que importa en esa lista.

    Los proyectos de los que el docente es autor no aparecen (conflicto de interés, spec 008).
    """
    base = (
        Proyecto.objects.exclude(autores=usuario)
        .select_related("asignatura", "revisor", "periodo").prefetch_related("autores")
    )
    eventos_a = lambda estado: Q(eventos__estado_nuevo=estado)  # noqa: E731

    pendientes = (
        base.filter(estado=Estado.ENVIADO)
        .annotate(fecha=Max("eventos__creado_en", filter=eventos_a(Estado.ENVIADO)),
                  envios=Count("eventos", filter=eventos_a(Estado.ENVIADO)))
        .order_by("fecha")  # los que más tiempo llevan esperando, primero
    )

    en_revision = base.filter(estado=Estado.EN_REVISION)
    if usuario.rol_activo == Rol.PROFESOR:
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
