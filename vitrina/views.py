"""Vistas públicas: portada, explorar, detalle de proyecto y verificación.

Todas las consultas públicas parten de Proyecto.objects.publicados(), que solo devuelve
proyectos aprobados (constitución, principio VI).
"""

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from proyectos.models import Estado, Proyecto, Tecnologia
from proyectos.permisos import puede_editar, puede_ver
from vitrina.forms import FormularioFiltros

POR_PAGINA = 12


def inicio(request):
    """Portada: qué es la plataforma, cifras reales, destacados y cómo funciona."""
    publicados = Proyecto.objects.publicados()
    cifras = {
        "verificados": publicados.count(),
        "autores": get_user_model().objects.filter(proyectos__in=publicados).distinct().count(),
        "tecnologias": Tecnologia.objects.filter(proyectos__in=publicados).distinct().count(),
    }
    destacados = publicados.con_relaciones().order_by("-aprobado_en", "-actualizado_en")[:3]
    pasos = [
        {"numero": "01", "titulo": _("Sube tu proyecto"),
         "texto": _("Descripción, coautores, tecnologías, repositorio y documento PDF.")},
        {"numero": "02", "titulo": _("Un docente lo revisa"),
         "texto": _("Lo aprueba, pide cambios o lo rechaza. Cada paso queda en el historial.")},
        {"numero": "03", "titulo": _("Queda verificado"),
         "texto": _("Se publica en la vitrina con el sello de la carrera y un código único.")},
        {"numero": "04", "titulo": _("Compártelo con QR"),
         "texto": _("Descarga el QR y el certificado PDF para tu portafolio.")},
    ]
    return render(request, "vitrina/inicio.html", {"pasos": pasos, "cifras": cifras, "destacados": destacados})


def explorar(request):
    """Listado público con búsqueda, filtros, orden y paginación de 12 en 12."""
    form = FormularioFiltros(request.GET or None)
    proyectos = form.filtrar(Proyecto.objects.publicados().con_relaciones())
    pagina = Paginator(proyectos, POR_PAGINA).get_page(request.GET.get("pagina"))

    # Cuántos proyectos publicados usa cada tecnología (para la barra de filtros)
    tecnologias = (
        Tecnologia.objects.annotate(total=Count("proyectos", filter=Q(proyectos__estado=Estado.APROBADO), distinct=True))
        .filter(total__gt=0)
        .order_by("-total", "nombre")
    )
    return render(request, "vitrina/explorar.html", {
        "form": form,
        "pagina": pagina,
        "total": pagina.paginator.count,
        "tecnologias": tecnologias,
        "seleccionadas": [str(t) for t in request.GET.getlist("tecnologia")],
        "filtros_activos": _filtros_activos(request, form),
    })


def _filtros_activos(request, form):
    """Lista de filtros aplicados, cada uno con la dirección que lo quita."""
    if not form.is_bound or not form.is_valid():
        return []
    datos, activos = form.cleaned_data, []

    def sin(parametro, valor=None):
        copia = request.GET.copy()
        copia.pop("pagina", None)
        if valor is None:
            copia.pop(parametro, None)
        else:
            copia.setlist(parametro, [v for v in copia.getlist(parametro) if v != str(valor)])
        return "?" + copia.urlencode() if copia else "?"

    if datos.get("q"):
        activos.append({"texto": f"“{datos['q']}”", "url": sin("q")})
    for tecnologia in datos.get("tecnologia") or []:
        activos.append({"texto": tecnologia.nombre, "url": sin("tecnologia", tecnologia.pk)})
    if datos.get("asignatura"):
        activos.append({"texto": datos["asignatura"].nombre, "url": sin("asignatura")})
    if datos.get("periodo"):
        activos.append({"texto": datos["periodo"], "url": sin("periodo")})
    return activos


def detalle(request, slug):
    """Detalle de un proyecto. Si no está aprobado, solo lo ven sus autores, profesores y admins."""
    proyecto = get_object_or_404(Proyecto.objects.con_relaciones(), slug=slug)
    if not puede_ver(request.user, proyecto):
        raise Http404  # para los demás, el proyecto "no existe"
    return render(request, "vitrina/detalle.html", {
        "proyecto": proyecto,
        "autorias": proyecto.autorias.select_related("usuario"),
        "puede_editar": puede_editar(request.user, proyecto),
    })


def verificar(request):
    """Verificación pública por código o QR. Llega en el módulo 005."""
    return render(request, "vitrina/proximamente.html", {
        "titulo": _("Verificar un proyecto"),
        "mensaje": _("Aquí vas a poder comprobar un proyecto con su código o escaneando su QR."),
    })
