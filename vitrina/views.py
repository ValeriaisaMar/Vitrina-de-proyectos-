"""Vistas públicas: portada, explorar, detalle de proyecto y verificación.

Todas las consultas públicas parten de Proyecto.objects.publicados(), que solo devuelve
proyectos aprobados (constitución, principio VI).
"""

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from cuentas.models import Rol
from proyectos.models import Estado, Proyecto, Tecnologia
from proyectos.permisos import puede_editar, puede_ver, puede_ver_historial
from proyectos.servicios import puede_cambiar
from vitrina.forms import FormularioFiltros, FormularioVerificar
from vitrina.verificacion import certificado_pdf, normalizar_codigo, qr_png, url_verificacion

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
    ver_historial = puede_ver_historial(request.user, proyecto)
    return render(request, "vitrina/detalle.html", {
        "proyecto": proyecto,
        "autorias": proyecto.autorias.select_related("usuario"),
        "puede_editar": puede_editar(request.user, proyecto),
        "puede_enviar": puede_cambiar(request.user, proyecto, Estado.ENVIADO),
        "es_docente": request.user.is_authenticated and request.user.rol in (Rol.PROFESOR, Rol.ADMIN),
        # El historial y las observaciones son internos: no se muestran al público
        "eventos": proyecto.eventos.select_related("actor") if ver_historial else None,
        "observacion": (
            proyecto.ultima_decision
            if ver_historial and proyecto.estado in (Estado.CON_OBSERVACIONES, Estado.RECHAZADO) else None
        ),
    })


def verificar(request):
    """Página Verificar: explica el QR y recibe un código escrito a mano."""
    form = FormularioVerificar(request.GET or None)
    if form.is_valid():
        return redirect("vitrina:verificar_codigo", codigo=form.cleaned_data["codigo"])
    pasos = [
        (_("Abre la cámara del celular"), _("No hace falta instalar nada: la cámara reconoce el QR.")),
        (_("Toca el enlace que aparece"), _("Te trae a la página de verificación de ese código.")),
        (_("Compara los datos"), _("Título, autores, docente y fecha deben coincidir con el certificado.")),
    ]
    return render(request, "vitrina/verificar.html", {"form": form, "pasos": pasos})


def verificar_codigo(request, codigo):
    """Resultado de la verificación: es la página a la que apunta el QR.

    Muestra SOLO datos públicos (constitución, VI): título, autores, docente, fecha y código.
    """
    canonico = normalizar_codigo(codigo)
    if canonico and canonico != codigo:
        return redirect("vitrina:verificar_codigo", codigo=canonico, permanent=True)
    proyecto = (
        Proyecto.objects.publicados().filter(codigo=canonico)
        .select_related("revisor").prefetch_related("autores").first()
        if canonico else None
    )
    contexto = {"proyecto": proyecto, "codigo": codigo, "form": FormularioVerificar()}
    # 404 si no existe: así los buscadores y otros sistemas también entienden que no es válido
    return render(request, "vitrina/verificado.html", contexto, status=200 if proyecto else 404)


def _proyecto_por_codigo(codigo):
    return get_object_or_404(Proyecto.objects.publicados().select_related("asignatura", "revisor"), codigo=codigo)


def descargar_qr(request, codigo):
    """PNG con el QR que lleva a la página de verificación."""
    proyecto = _proyecto_por_codigo(codigo)
    respuesta = HttpResponse(qr_png(url_verificacion(request, proyecto.codigo)), content_type="image/png")
    if "descargar" in request.GET:  # en el detalle se muestra; con ?descargar se baja como archivo
        respuesta["Content-Disposition"] = f'attachment; filename="{proyecto.codigo}-qr.png"'
    return respuesta


def descargar_certificado(request, codigo):
    """Certificado en PDF, en el idioma con el que se navega."""
    proyecto = _proyecto_por_codigo(codigo)
    pdf = certificado_pdf(proyecto, url_verificacion(request, proyecto.codigo))
    respuesta = HttpResponse(pdf, content_type="application/pdf")
    respuesta["Content-Disposition"] = f'attachment; filename="{proyecto.codigo}-certificado.pdf"'
    return respuesta
