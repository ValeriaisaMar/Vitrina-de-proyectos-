"""Validaciones de los datos y archivos que suben los estudiantes (constitución, principio III)."""

import re
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

MAX_PDF_MB = 10
MAX_IMAGEN_MB = 3
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}
MB = 1024 * 1024

# Solo http y https: el validador de Django acepta también ftp por defecto.
validar_url_web = URLValidator(schemes=["http", "https"], message=_("Escribe un enlace que empiece por http:// o https://."))


def validar_pdf(archivo):
    """El documento debe ser un PDF real de hasta 10 MB.

    No basta con la extensión: un PDF siempre empieza con los bytes "%PDF-", así que se
    leen los primeros bytes para confirmarlo.
    """
    if archivo.size > MAX_PDF_MB * MB:
        raise ValidationError(_("El PDF pesa más de %(mb)s MB.") % {"mb": MAX_PDF_MB}, code="pdf_grande")
    if Path(archivo.name).suffix.lower() != ".pdf":
        raise ValidationError(_("El documento debe ser un archivo PDF."), code="pdf_extension")
    posicion = archivo.tell() if hasattr(archivo, "tell") else 0
    archivo.seek(0)
    cabecera = archivo.read(5)
    archivo.seek(posicion)
    if cabecera != b"%PDF-":
        raise ValidationError(_("El archivo no es un PDF válido."), code="pdf_invalido")


def validar_imagen(archivo):
    """Cada imagen debe ser JPG, PNG o WEBP y pesar hasta 3 MB.

    Que el contenido sea de verdad una imagen lo comprueba ImageField con Pillow.
    """
    if archivo.size > MAX_IMAGEN_MB * MB:
        raise ValidationError(
            _("La imagen %(nombre)s pesa más de %(mb)s MB.") % {"nombre": archivo.name, "mb": MAX_IMAGEN_MB},
            code="imagen_grande",
        )
    if Path(archivo.name).suffix.lower() not in EXTENSIONES_IMAGEN:
        raise ValidationError(
            _("La imagen %(nombre)s debe ser JPG, PNG o WEBP.") % {"nombre": archivo.name},
            code="imagen_extension",
        )


_PATRON_PERIODO = re.compile(r"^\d{4}-[12]$")


def validar_periodo(valor):
    """El periodo académico se escribe AAAA-1 o AAAA-2 (por ejemplo 2026-2)."""
    if not _PATRON_PERIODO.match(valor or ""):
        raise ValidationError(_("El periodo debe tener la forma AAAA-1 o AAAA-2."), code="periodo")
