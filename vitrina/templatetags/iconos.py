"""Íconos SVG y utilidades de texto para las plantillas (spec 009).

Uso en cualquier plantilla (está registrada como *builtin* en settings, no hace falta {% load %}):

    {% icono "bookmark" %}                     → decorativo: aria-hidden="true", 20 px
    {% icono "external-link" tam=16 clase="shrink-0" %}
    {% icono "x" etiqueta=_("Cerrar") %}       → con significado propio: role="img" y aria-label

Los SVG viven en static/iconos/ (Tabler Icons, MIT, y logos de Simple Icons, CC0). Se insertan en
línea para que tomen el color del texto (currentColor) y cambien solos con el modo oscuro.
mark_safe solo se usa sobre archivos del repositorio, nunca sobre contenido de usuarios.
"""

import hashlib
import logging
import os
import re
import unicodedata
from functools import lru_cache

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()
logger = logging.getLogger(__name__)

_NOMBRE_VALIDO = re.compile(r"^[a-z0-9-]+$")


@lru_cache(maxsize=256)
def _svg(nombre):
    """Lee static/iconos/<nombre>.svg una sola vez por proceso. "" si no existe."""
    if not _NOMBRE_VALIDO.match(nombre):
        return ""
    ruta = finders.find(f"iconos/{nombre}.svg")
    if not ruta:
        logger.warning("No existe el ícono %s", nombre)
        return ""
    with open(ruta, encoding="utf-8") as archivo:
        return archivo.read().strip()


@lru_cache(maxsize=64)
def _huella(ruta, modificado):
    """Primeros 10 caracteres del hash del archivo. Se recalcula solo si cambia la fecha del archivo."""
    with open(ruta, "rb") as archivo:
        return hashlib.sha256(archivo.read()).hexdigest()[:10]


@register.simple_tag
def estatico(ruta):
    """Como {% static %}, pero con ?v=<huella del archivo> al final.

    Sin esto, el navegador sigue usando un app.css o un menu.js viejos guardados en su caché después
    de actualizar el código: aparecen clases que "no existen" (el menú sin posición, el modo oscuro
    que esconde textos, fotos estiradas). Con la huella, cada versión nueva tiene otra dirección y
    el navegador la descarga sola. Uso: <link rel="stylesheet" href="{% estatico 'css/app.css' %}">
    """
    url = static(ruta)
    archivo = finders.find(ruta)
    if not archivo:
        return url
    try:
        return f"{url}?v={_huella(archivo, os.path.getmtime(archivo))}"
    except OSError:
        return url


@register.simple_tag
def icono(nombre, tam=20, clase="", etiqueta=""):
    """Devuelve el SVG del ícono con tamaño, clases y accesibilidad."""
    svg = _svg(str(nombre))
    if not svg:
        return ""
    try:
        tam = int(tam)
    except (TypeError, ValueError):
        tam = 20
    atributos = f'width="{tam}" height="{tam}" focusable="false"'
    if clase:
        atributos += f' class="{escape(clase)}"'
    if etiqueta:
        atributos += f' role="img" aria-label="{escape(etiqueta)}"'
    else:
        atributos += ' aria-hidden="true"'
    return mark_safe(svg.replace("<svg ", f"<svg {atributos} ", 1))


@register.filter
def inicial(texto):
    """Primera letra visible del texto, en mayúscula, para la portada de color.

    Normaliza a NFC y toma el primer carácter base junto con sus marcas combinantes: así una
    «Ñ» escrita como N + tilde no se parte en dos (eso es lo que salía como cajita).
    """
    texto = unicodedata.normalize("NFC", str(texto or "")).lstrip()
    if not texto:
        return ""
    fin = 1
    while fin < len(texto) and unicodedata.combining(texto[fin]):
        fin += 1
    # Signos como ¿ o ¡ al inicio no sirven de inicial: se busca la primera letra o número
    for i, caracter in enumerate(texto):
        if caracter.isalnum():
            fin = i + 1
            while fin < len(texto) and unicodedata.combining(texto[fin]):
                fin += 1
            return unicodedata.normalize("NFC", texto[i:fin]).upper()
    return texto[:fin].upper()


@register.filter(name="nfc")
def nfc_filtro(texto):
    """El texto en forma compuesta (NFC): «ñ» como un solo carácter y no como n + tilde.

    Las fuentes web dibujan mejor la forma compuesta; la usa la portada de color con el título.
    """
    return unicodedata.normalize("NFC", str(texto)) if texto is not None else ""
