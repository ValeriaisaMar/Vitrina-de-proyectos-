"""Vistas públicas: portada, explorar, detalle de proyecto y verificación.

Todas las consultas públicas parten de Proyecto.objects.publicados(), que solo devuelve
proyectos aprobados (constitución, principio VI).
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from comunidad.consultas import datos_comunidad
from cuentas.models import Aptitud, Perfil, Rol
from cuentas.perfiles import buscar_personas, editar_seccion, formularios_de_edicion, personas_relacionadas
from proyectos.models import Estado, Proyecto, Tecnologia
from proyectos.permisos import puede_editar, puede_ver, puede_ver_historial
from proyectos import solicitudes
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
    destacados = (
        publicados.con_relaciones().annotate(total_me_gusta=Count("me_gustas", distinct=True))
        .order_by("-aprobado_en", "-actualizado_en")[:3]
    )
    pasos = [
        {"numero": "01", "titulo": _("Sube tu proyecto"),
         "texto": _("Descripción, coautores, tecnologías, repositorio y documento PDF.")},
        {"numero": "02", "titulo": _("Un docente lo revisa"),
         "texto": _("Eliges al docente que lo revisa. Lo aprueba, pide cambios o lo rechaza, y cada paso queda en el historial.")},
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
    # Bloque "Personas": perfiles cuyo nombre coincide con la búsqueda (spec 009)
    texto = form.cleaned_data.get("q", "") if form.is_bound and form.is_valid() else ""
    return render(request, "vitrina/explorar.html", {
        "personas": buscar_personas(texto) if texto and not request.GET.get("pagina") else [],
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
        activos.append({"texto": datos["periodo"].nombre, "url": sin("periodo")})
    return activos


def detalle(request, slug):
    """Detalle de un proyecto. Si no está aprobado, solo lo ven sus autores, profesores y admins."""
    proyecto = get_object_or_404(Proyecto.objects.con_relaciones(), slug=slug)
    if not puede_ver(request.user, proyecto):
        raise Http404  # para los demás, el proyecto "no existe"
    ver_historial = puede_ver_historial(request.user, proyecto)
    return render(request, "vitrina/detalle.html", {
        "revision": _estado_revision(request.user, proyecto),
        # Vista previa al compartir el enlace (WhatsApp, LinkedIn…), solo si está publicado (spec 008)
        **(_vista_previa(request, proyecto) if proyecto.publicado else {}),
        # Me gusta, guardados y comentarios: solo en proyectos publicados (módulo 007)
        "comunidad": datos_comunidad(request.user, proyecto) if proyecto.publicado else None,
        "proyecto": proyecto,
        # perfil y roles precargados: el enlace a cada perfil no cuesta consultas extra (spec 009)
        "autorias": proyecto.autorias.select_related("usuario__perfil").prefetch_related("usuario__roles_asignados"),
        "puede_editar": puede_editar(request.user, proyecto),
        "puede_enviar": puede_cambiar(request.user, proyecto, Estado.ENVIADO),
        "es_docente": request.user.is_authenticated and request.user.es_docente,
        # El historial y las observaciones son internos: no se muestran al público
        "eventos": proyecto.eventos.select_related("actor", "profesor") if ver_historial else None,
        "observacion": (
            proyecto.ultima_decision
            if ver_historial and proyecto.estado in (Estado.CON_OBSERVACIONES, Estado.RECHAZADO) else None
        ),
    })


def _estado_revision(usuario, proyecto):
    """Para los autores de un proyecto Enviado: a quién se le pidió, si puede retirar o elegir (spec 009)."""
    if proyecto.estado != Estado.ENVIADO or not proyecto.es_autor(usuario):
        return None
    pendiente = proyecto.solicitud_pendiente
    return {
        "subestado": proyecto.subestado,
        "pendiente": pendiente,
        "puede_retirar": bool(pendiente) and solicitudes.puede_retirar(usuario, pendiente),
        "puede_elegir": solicitudes.puede_elegir_revisor(usuario, proyecto),
        "recomendacion": solicitudes.recomendacion_vigente(proyecto) if not pendiente else None,
    }


def _vista_previa(request, proyecto):
    """Datos Open Graph del proyecto: título, resumen y portada con dirección absoluta."""
    imagen = proyecto.url_imagen_compartir  # la portada; si no hay, la primera captura (spec 009)
    return {
        "og_titulo": proyecto.titulo,
        "og_descripcion": proyecto.resumen,
        "og_imagen": request.build_absolute_uri(imagen) if imagen else None,
    }


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
        .select_related("revisor", "periodo", "periodo_aprobacion").prefetch_related("autores").first()
        if canonico else None
    )
    contexto = {"proyecto": proyecto, "codigo": codigo, "form": FormularioVerificar()}
    # 404 si no existe: así los buscadores y otros sistemas también entienden que no es válido
    return render(request, "vitrina/verificado.html", contexto, status=200 if proyecto else 404)


def _proyecto_por_codigo(codigo):
    return get_object_or_404(Proyecto.objects.publicados().select_related("asignatura", "revisor", "periodo", "periodo_aprobacion"), codigo=codigo)


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


# --------------------------------------------------------------------------- Perfil público (spec 009, historia 4)


def persona(request, slug):
    """Perfil público de una persona. El dueño lo edita aquí mismo, sección por sección.

    - Lo ve cualquiera (también sin sesión) si la persona tiene rol estudiante o profesor.
    - Quien solo es admin no tiene perfil visible: 404.
    - POST: solo el dueño. Cada formulario manda "seccion" (descripcion, aptitudes, foto…). Si hay
      errores se vuelve a mostrar la página con lo que escribió; si no, se redirige (PRG).
    """
    perfil = get_object_or_404(
        Perfil.objects.select_related("usuario").prefetch_related("usuario__roles_asignados"), slug=slug,
    )
    usuario = perfil.usuario
    if not usuario.tiene_perfil_publico:
        raise Http404
    es_dueno = request.user.is_authenticated and request.user.pk == usuario.pk
    ligado = None

    if request.method == "POST":
        if not es_dueno:
            raise PermissionDenied
        seccion = request.POST.get("seccion", "")
        ok, resultado = editar_seccion(perfil, seccion, request.POST, request.FILES)
        if ok:
            messages.success(request, resultado)
            return redirect(f"{perfil.get_absolute_url()}?editar=1#{seccion.replace('quitar_', '')}")
        if resultado is None:
            raise PermissionDenied
        ligado = resultado

    editando = es_dueno and (ligado is not None or "editar" in request.GET)
    proyectos = (
        Proyecto.objects.publicados().filter(autorias__usuario=usuario).con_relaciones()
        .annotate(total_me_gusta=Count("me_gustas", distinct=True)).order_by("-aprobado_en")
    )
    es_profesor = usuario.tiene_rol(Rol.PROFESOR)
    return render(request, "vitrina/persona.html", {
        "perfil": perfil,
        "persona": usuario,
        "es_dueno": es_dueno,
        "editando": editando,
        "es_profesor": es_profesor,
        "aptitudes": list(perfil.aptitudes.all()),
        "experiencias": list(perfil.experiencias.all()),
        "estudios": list(perfil.estudios.all()),
        "asignaturas": list(perfil.asignaturas_imparte.select_related("plan").order_by("semestre", "nombre")) if es_profesor else [],
        "proyectos": proyectos,
        "relacionados": personas_relacionadas(usuario),
        "formularios": formularios_de_edicion(perfil, ligado) if editando else None,
        "aptitudes_existentes": Aptitud.objects.values_list("nombre", flat=True)[:300] if editando else [],
        "og_titulo": usuario.nombre_completo,
        "og_descripcion": perfil.descripcion[:200] or usuario.rol_publico,
        "og_imagen": request.build_absolute_uri(perfil.foto.url) if perfil.foto else None,
    })
