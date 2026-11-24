"""Vistas públicas de la vitrina.

En el módulo 001 solo existe la portada. Explorar y Verificar muestran una página
"Próximamente" que los módulos 003 y 005 reemplazan.
"""

from django.shortcuts import render
from django.utils.translation import gettext as _


def inicio(request):
    """Portada: qué es la plataforma, cómo funciona y una invitación a crear cuenta."""
    pasos = [
        {
            "numero": "01",
            "titulo": _("Sube tu proyecto"),
            "texto": _("Descripción, coautores, tecnologías, repositorio y documento PDF."),
        },
        {
            "numero": "02",
            "titulo": _("Un docente lo revisa"),
            "texto": _("Lo aprueba, pide cambios o lo rechaza. Cada paso queda en el historial."),
        },
        {
            "numero": "03",
            "titulo": _("Queda verificado"),
            "texto": _("Se publica en la vitrina con el sello de la carrera y un código único."),
        },
        {
            "numero": "04",
            "titulo": _("Compártelo con QR"),
            "texto": _("Descarga el QR y el certificado PDF para tu portafolio."),
        },
    ]
    return render(request, "vitrina/inicio.html", {"pasos": pasos})


def explorar(request):
    """Listado público de proyectos verificados. Llega en el módulo 003."""
    return render(request, "vitrina/proximamente.html", {
        "titulo": _("Explorar proyectos"),
        "mensaje": _("Aquí vas a poder buscar y filtrar los proyectos verificados de la carrera."),
    })


def verificar(request):
    """Verificación pública por código o QR. Llega en el módulo 005."""
    return render(request, "vitrina/proximamente.html", {
        "titulo": _("Verificar un proyecto"),
        "mensaje": _("Aquí vas a poder comprobar un proyecto con su código o escaneando su QR."),
    })
