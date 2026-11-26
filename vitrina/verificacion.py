"""Código de verificación, QR y certificado PDF de los proyectos aprobados (constitución, VI).

Todo se genera en memoria al momento de pedirlo: no se guardan archivos, así el QR y el
certificado siempre coinciden con lo que dice la base de datos.
"""

import io
import re
from pathlib import Path

import qrcode
from django.conf import settings
from django.contrib.staticfiles import finders
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.translation import gettext as _
from qrcode.constants import ERROR_CORRECT_M
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from config.texto import nfc, para_pdf

VERDE = HexColor("#025a27")
VERDE_PROFUNDO = HexColor("#01401b")
AMARILLO = HexColor("#ecb932")
TINTA = HexColor("#0f1f17")
SUAVE = HexColor("#4b5b52")
TINTE = HexColor("#e6efe9")

_PATRON = re.compile(r"VP-?(\d{4})-?(\d{4,})")


# --------------------------------------------------------------------------- Código y dirección


def normalizar_codigo(texto):
    """Convierte lo que escribió la persona en un código canónico, o None si no tiene la forma.

    "  vp-2026-0007 " → "VP-2026-0007"; "VP20260007" → "VP-2026-0007"; "hola" → None.
    Validar la forma antes de consultar evita búsquedas inútiles con texto arbitrario.
    """
    limpio = re.sub(r"\s+", "", texto or "").upper()
    coincidencia = _PATRON.fullmatch(limpio)
    if not coincidencia:
        return None
    anio, numero = coincidencia.groups()
    return f"VP-{anio}-{numero}"


def url_verificacion(request, codigo):
    """Dirección absoluta de la página de verificación, la que va dentro del QR.

    Si SITIO_URL está en el .env se usa esa base (útil en la demo, cuando el celular entra por la
    IP del portátil); si no, la dirección con la que se hizo la petición.
    """
    ruta = reverse("vitrina:verificar_codigo", args=[codigo])
    if settings.SITIO_URL:
        return settings.SITIO_URL + ruta
    return request.build_absolute_uri(ruta)


# --------------------------------------------------------------------------- QR


def qr_png(url):
    """Devuelve los bytes de un PNG con el QR de la dirección, en el verde institucional.

    Nivel de corrección M: el QR se sigue leyendo aunque se dañe hasta un 15 % (impreso, doblado).
    """
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=12, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="#025a27", back_color="white")
    salida = io.BytesIO()
    imagen.save(salida, format="PNG")
    return salida.getvalue()


# --------------------------------------------------------------------------- Certificado

_FUENTES = {"texto": "archivo-400", "negrita": "archivo-700", "titulo": "unbounded-800"}


def _registrar_fuentes():
    """reportlab no lee woff2: usa las mismas fuentes del sitio convertidas a TTF."""
    carpeta = Path(settings.BASE_DIR) / "static" / "fonts" / "pdf"
    for nombre in _FUENTES.values():
        if nombre not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(nombre, str(carpeta / f"{nombre}.ttf")))


def _imagen(*nombres):
    """La primera imagen que exista en static/ como ImageReader, o None. reportlab no lee SVG ni webp."""
    for nombre in nombres:
        ruta = finders.find(nombre)
        if ruta:
            return ImageReader(ruta)
    return None


def _logo():
    """Logo UTEQ en blanco, para la banda verde del certificado (spec 008)."""
    return _imagen("img/marca/uteq-blanco-grande.png", "img/logo-uteq-blanco.png", "img/marca/uteq-verde-pdf.png", "img/logo-uteq.png")


def _sellos():
    """Sellos de la Facultad y de la Carrera en PNG grande (marca/*-pdf.png)."""
    return [s for s in (_imagen("img/marca/sello-facultad-pdf.png"), _imagen("img/marca/sello-carrera-pdf.png")) if s]


def _seguro(texto, fuente):
    """El texto listo para dibujar con esa fuente: NFC y sin caracteres que la fuente no trae.

    reportlab no busca otra fuente cuando falta un carácter (el navegador sí): dibuja una caja
    con una x. config.texto.para_pdf cambia esos caracteres por uno parecido (spec 009).
    """
    glifos = pdfmetrics.getFont(fuente).face.charToGlyph
    return para_pdf(texto, lambda caracter: ord(caracter) in glifos)


def _parrafo(c, texto, fuente, tamano, x, y, ancho, interlineado=1.25, color=TINTA):
    """Escribe un texto partido en líneas dentro de un ancho. Devuelve la y de la última línea."""
    c.setFont(fuente, tamano)
    c.setFillColor(color)
    texto = _seguro(texto, fuente)
    for linea in simpleSplit(texto, fuente, tamano, ancho):
        c.drawString(x, y, linea)
        y -= tamano * interlineado
    return y + tamano * interlineado


def certificado_pdf(proyecto, url):
    """Dibuja el certificado (A4 horizontal) y devuelve los bytes del PDF.

    Los textos usan el idioma activo: si la persona navega en inglés, sale en inglés.
    """
    _registrar_fuentes()
    texto, negrita, titulo = _FUENTES["texto"], _FUENTES["negrita"], _FUENTES["titulo"]
    ancho, alto = landscape(A4)
    salida = io.BytesIO()
    c = canvas.Canvas(salida, pagesize=(ancho, alto))
    c.setTitle(_("Certificado %(codigo)s") % {"codigo": proyecto.codigo})
    c.setAuthor("Vitrina de Proyectos · UTEQ")
    c.setSubject(nfc(proyecto.titulo))

    margen = 30
    # Sombra dura verde y marco con borde de tinta: el mismo neo-brutalismo de la web
    c.setFillColor(VERDE)
    c.rect(margen + 8, margen - 8, ancho - 2 * margen, alto - 2 * margen, stroke=0, fill=1)
    c.setFillColor(white)
    c.setStrokeColor(TINTA)
    c.setLineWidth(2.5)
    c.rect(margen, margen, ancho - 2 * margen, alto - 2 * margen, stroke=1, fill=1)

    # Encabezado verde con la universidad
    banda = 78
    tope = alto - margen
    c.setFillColor(VERDE)
    c.rect(margen, tope - banda, ancho - 2 * margen, banda, stroke=1, fill=1)
    x = margen + 32
    logo = _logo()
    if logo:
        ancho_img, alto_img = logo.getSize()
        alto_logo = 38
        ancho_logo = ancho_img * alto_logo / alto_img
        c.drawImage(logo, x, tope - banda + (banda - alto_logo) / 2, width=ancho_logo, height=alto_logo, mask="auto")
        x += ancho_logo + 22
        # Línea fina amarilla que separa el logo del nombre de la universidad
        c.setFillColor(AMARILLO)
        c.rect(x - 11, tope - banda + 18, 2, banda - 36, stroke=0, fill=1)
    # Sellos de la Facultad y de la Carrera a la derecha de la banda, sobre un círculo blanco
    lado_sello = 58
    x_sello = ancho - margen - 32 - lado_sello
    for sello in reversed(_sellos()):
        centro_x, centro_y = x_sello + lado_sello / 2, tope - banda / 2
        c.setFillColor(white)
        c.circle(centro_x, centro_y, lado_sello / 2 + 1.5, stroke=0, fill=1)
        c.drawImage(sello, x_sello, centro_y - lado_sello / 2, width=lado_sello, height=lado_sello, mask="auto")
        x_sello -= lado_sello + 12
    c.setFillColor(white)
    c.setFont(titulo, 15)
    c.drawString(x, tope - 36, _("Universidad Técnica Estatal de Quevedo").upper())
    c.setFont(texto, 11)
    c.setFillColor(HexColor("#cfe3d6"))
    c.drawString(x, tope - 56, _("Facultad de Ciencias de la Computación · Ingeniería de Software"))

    # Columna derecha: QR y código
    lado_qr = 168
    x_qr = ancho - margen - 32 - lado_qr
    y_qr = margen + 92
    c.setFillColor(white)
    c.setStrokeColor(TINTA)
    c.setLineWidth(2)
    c.rect(x_qr - 8, y_qr - 8, lado_qr + 16, lado_qr + 16, stroke=1, fill=1)
    c.drawImage(ImageReader(io.BytesIO(qr_png(url))), x_qr, y_qr, lado_qr, lado_qr)
    c.setFont(titulo, 17)
    c.setFillColor(TINTA)
    c.drawCentredString(x_qr + lado_qr / 2, y_qr - 38, proyecto.codigo)
    c.setFillColor(AMARILLO)  # acento amarillo discreto bajo el código
    c.rect(x_qr + 24, y_qr - 46, lado_qr - 48, 3.5, stroke=0, fill=1)
    c.setFont(texto, 8.5)
    c.setFillColor(SUAVE)
    c.drawCentredString(x_qr + lado_qr / 2, y_qr - 62, _("Escanea para verificar"))

    # Cuerpo del certificado
    x = margen + 40
    ancho_texto = x_qr - x - 50
    y = tope - banda - 50
    c.setFont(negrita, 10)
    c.setFillColor(VERDE)
    c.drawString(x, y, _("CERTIFICADO DE PROYECTO VERIFICADO"))
    c.setFillColor(AMARILLO)
    c.rect(x, y - 9, 56, 3.5, stroke=0, fill=1)

    y -= 40
    c.setFont(texto, 12)
    c.setFillColor(SUAVE)
    c.drawString(x, y, _("Se certifica que el proyecto"))
    y = _parrafo(c, proyecto.titulo, titulo, 24, x, y - 34, ancho_texto, interlineado=1.2)

    y -= 34
    autores = ", ".join(a.nombre_completo for a in proyecto.autores.all())
    c.setFont(texto, 12)
    c.setFillColor(SUAVE)
    c.drawString(x, y, _("desarrollado por"))
    y = _parrafo(c, autores, negrita, 14, x, y - 22, ancho_texto)

    y -= 30
    fecha = formats.date_format(timezone.localtime(proyecto.aprobado_en), "DATE_FORMAT")
    docente = proyecto.revisor.nombre_completo if proyecto.revisor else _("un docente de la carrera")
    frase = _("en la asignatura %(asignatura)s, periodo %(periodo)s, fue revisado y aprobado por %(docente)s el %(fecha)s, y forma parte de la Vitrina de Proyectos de la carrera.") % {"asignatura": proyecto.asignatura.nombre, "periodo": (proyecto.periodo_aprobacion or proyecto.periodo).nombre, "docente": docente, "fecha": fecha}
    _parrafo(c, frase, texto, 12, x, y, ancho_texto, interlineado=1.45)

    # Pie: cómo comprobarlo
    c.setStrokeColor(TINTE)
    c.setLineWidth(1)
    c.line(x, margen + 58, x_qr - 40, margen + 58)
    c.setFont(texto, 8.5)
    c.setFillColor(SUAVE)
    c.drawString(x, margen + 42, _("Este certificado se comprueba en línea. Si los datos no coinciden con la página de verificación, no es válido."))
    c.setFont(negrita, 8.5)
    c.setFillColor(VERDE)
    c.drawString(x, margen + 28, url)

    c.showPage()
    c.save()
    return salida.getvalue()
