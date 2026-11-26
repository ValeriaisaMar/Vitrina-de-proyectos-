"""Panel de cada rol (módulo 006): la página a la que llega cada persona al iniciar sesión.

Una sola URL, /panel/, que arma un resumen distinto según el rol. Cada panel cuenta en la base de
datos (aggregate, annotate) en vez de recorrer listas en Python: así hace pocas consultas aunque
haya muchos proyectos.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Prefetch, Q
from django.shortcuts import render
from django.utils import timezone

from cuentas.models import ConfiguracionCorreo, Rol
from proyectos.models import (
    ESTADOS_DE_DECISION,
    Estado,
    EstadoSolicitud,
    EventoEstado,
    Periodo,
    PlanEstudio,
    Proyecto,
    SolicitudRevision,
    Tecnologia,
)
from proyectos.servicios import consultas_bandeja

Usuario = get_user_model()
DIAS_DE_ESPERA = 3  # desde cuántos días un proyecto enviado se considera "atrasado"


def _contar(campo, valor):
    """Count condicional: cuántas filas cumplen campo=valor (o campo__in=valor si es lista)."""
    filtro = {f"{campo}__in": valor} if isinstance(valor, (list, tuple, set)) else {campo: valor}
    return Count("id", filter=Q(**filtro), distinct=True)


def _barras(filas):
    """Convierte [(etiqueta, valor), ...] en filas con el ancho de su barra (0 a 100 %).

    La barra más larga ocupa el 100 %; las demás, en proporción. El número se escribe siempre
    al lado, así que la barra nunca es la única forma de leer el dato.
    """
    maximo = max((valor for _, valor in filas), default=0)
    return [
        {"etiqueta": etiqueta, "valor": valor, "ancho": round(valor * 100 / maximo) if maximo else 0}
        for etiqueta, valor in filas
    ]


@login_required
def panel(request):
    """Muestra el panel del rol con el que actúa la persona (rol activo, spec 008)."""
    if request.user.rol_activo == Rol.ADMIN:
        return _panel_admin(request)
    if request.user.rol_activo == Rol.PROFESOR:
        return _panel_profesor(request)
    return _panel_estudiante(request)


# --------------------------------------------------------------------------- Estudiante


def _panel_estudiante(request):
    mios = Proyecto.objects.de_autor(request.user)
    cifras = mios.aggregate(
        borradores=_contar("estado", Estado.BORRADOR),
        en_revision=_contar("estado", [Estado.ENVIADO, Estado.EN_REVISION]),
        observaciones=_contar("estado", Estado.CON_OBSERVACIONES),
        aprobados=_contar("estado", Estado.APROBADO),
        total=Count("id", distinct=True),
    )
    # La última observación de cada proyecto llega en una sola consulta extra (Prefetch)
    observaciones = EventoEstado.objects.filter(estado_nuevo=Estado.CON_OBSERVACIONES).select_related("actor").order_by("-creado_en")
    corregir = (
        mios.filter(estado=Estado.CON_OBSERVACIONES)
        .prefetch_related(Prefetch("eventos", queryset=observaciones, to_attr="observaciones"))
        .order_by("-actualizado_en")
    )
    # Spec 009: enviados sin revisor ni solicitud pendiente, de los que es creador (debe elegir)
    elegir_revisor = (
        mios.filter(estado=Estado.ENVIADO, revisor__isnull=True, autorias__usuario=request.user, autorias__es_creador=True)
        .con_subestado().filter(tiene_solicitud_pendiente=False).order_by("-actualizado_en")
    )
    return render(request, "vitrina/paneles/estudiante.html", {
        "elegir_revisor": elegir_revisor,
        "cifras": cifras,
        "corregir": corregir,
        "borradores": mios.filter(estado=Estado.BORRADOR).select_related("asignatura").order_by("-actualizado_en"),
        "aprobados": mios.filter(estado=Estado.APROBADO).order_by("-aprobado_en"),
    })


# --------------------------------------------------------------------------- Profesor


def _panel_profesor(request):
    bandeja = consultas_bandeja(request.user)
    decisiones = EventoEstado.objects.filter(actor=request.user).aggregate(
        aprobados=_contar("estado_nuevo", Estado.APROBADO),
        observaciones=_contar("estado_nuevo", Estado.CON_OBSERVACIONES),
        rechazados=_contar("estado_nuevo", Estado.RECHAZADO),
    )
    return render(request, "vitrina/paneles/profesor.html", {
        "solicitudes_pendientes": SolicitudRevision.objects.filter(profesor=request.user, estado=EstadoSolicitud.PENDIENTE).count(),
        "por_revisar": bandeja["pendientes"].count(),
        "mis_revisiones": bandeja["en_revision"].count(),
        "decisiones": decisiones,
        "esperando": bandeja["pendientes"][:3],
        "en_curso": bandeja["en_revision"][:5],
        "recientes": (
            EventoEstado.objects.filter(actor=request.user, estado_nuevo__in=ESTADOS_DE_DECISION)
            .select_related("proyecto").order_by("-creado_en")[:5]
        ),
    })


# --------------------------------------------------------------------------- Admin


def _correo_envio():
    """Desde qué correo salen los mensajes, si el admin lo configuró en la app (spec 008)."""
    configuracion = ConfiguracionCorreo.actual()
    return configuracion.remitente if configuracion else None


def _panel_admin(request):
    # Cuántas cuentas activas TIENEN cada rol (una persona con dos roles cuenta en los dos)
    con_rol = lambda rol: Count("id", filter=Q(roles_asignados__rol=rol, is_active=True), distinct=True)  # noqa: E731
    usuarios = Usuario.objects.aggregate(
        estudiantes=con_rol(Rol.ESTUDIANTE),
        profesores=con_rol(Rol.PROFESOR),
        admins=con_rol(Rol.ADMIN),
        sin_activar=Count("id", filter=Q(is_active=False, last_login__isnull=True), distinct=True),
    )

    por_estado = dict(Proyecto.objects.values_list("estado").annotate(n=Count("id")))
    estados = _barras([(etiqueta, por_estado.get(valor, 0)) for valor, etiqueta in Estado.choices])

    limite = timezone.now() - timedelta(days=DIAS_DE_ESPERA)
    atrasados = (
        Proyecto.objects.filter(estado=Estado.ENVIADO)
        .annotate(enviado_en=Max("eventos__creado_en", filter=Q(eventos__estado_nuevo=Estado.ENVIADO)))
        .filter(enviado_en__lt=limite).order_by("enviado_en")
    )

    # Aprobados por período de aprobación (spec 009), del más reciente al más antiguo
    periodos = _barras(list(
        Periodo.objects.annotate(n=Count("proyectos_aprobados", filter=Q(proyectos_aprobados__estado=Estado.APROBADO)))
        .filter(n__gt=0).order_by("-fecha_inicio", "-id").values_list("nombre", "n")[:6]
    ))
    tecnologias = _barras(list(
        Tecnologia.objects.annotate(n=Count("proyectos", filter=Q(proyectos__estado=Estado.APROBADO)))
        .filter(n__gt=0).order_by("-n", "nombre").values_list("nombre", "n")[:6]
    ))

    return render(request, "vitrina/paneles/admin.html", {
        "usuarios": usuarios,
        "total_proyectos": sum(por_estado.values()),
        "estados": estados,
        "atrasados": atrasados[:5],
        "total_atrasados": atrasados.count(),
        "dias_espera": DIAS_DE_ESPERA,
        "periodos": periodos,
        "periodo_actual_panel": Periodo.actual(),
        "planes_activos": PlanEstudio.objects.filter(activo=True).count(),
        "correo_envio": _correo_envio(),
        "tecnologias": tecnologias,
        "actividad": EventoEstado.objects.select_related("proyecto", "actor").order_by("-creado_en")[:8],
    })
