"""Imágenes que suben las personas: foto de perfil y portada del proyecto (spec 009).

Dos pasos:
1. validar_imagen_subida(): extensión, tamaño (máx. 5 MB) y que Pillow la abra como una imagen real
   JPG, PNG o WEBP. La extensión sola no prueba nada: un .jpg puede ser cualquier cosa.
2. convertir_a_webp(): corrige la orientación de la cámara, recorta al centro a la medida pedida y
   la guarda como webp con un nombre aleatorio. Al volver a dibujar la imagen se pierden los
   metadatos (por ejemplo, la ubicación GPS de la foto) y cualquier contenido extra del archivo.
"""

import io
import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_MB = 5
MB = 1024 * 1024
EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}
FORMATOS = {"JPEG", "PNG", "WEBP"}

# Medidas finales (ancho, alto)
TAM_PORTADA = (1200, 675)  # 16:9
TAM_FOTO = (400, 400)


def validar_imagen_subida(archivo, max_mb=MAX_MB):
    """Lanza ValidationError si el archivo no es una imagen JPG, PNG o WEBP real de hasta max_mb."""
    if archivo.size > max_mb * MB:
        raise ValidationError(_("La imagen pesa más de %(mb)s MB.") % {"mb": max_mb}, code="imagen_grande")
    if Path(archivo.name or "").suffix.lower() not in EXTENSIONES:
        raise ValidationError(_("La imagen debe ser JPG, PNG o WEBP."), code="imagen_extension")
    try:
        archivo.seek(0)
        with Image.open(archivo) as imagen:
            formato = imagen.format
            imagen.verify()  # revisa la estructura del archivo sin decodificarlo entero
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ValidationError(_("El archivo no es una imagen válida."), code="imagen_invalida")
    finally:
        archivo.seek(0)
    if formato not in FORMATOS:
        raise ValidationError(_("La imagen debe ser JPG, PNG o WEBP."), code="imagen_formato")


def convertir_a_webp(archivo, tam):
    """Devuelve un ContentFile webp de tamaño `tam` (recorte centrado) con nombre aleatorio."""
    archivo.seek(0)
    with Image.open(archivo) as original:  # verify() deja la imagen inservible: se abre de nuevo
        imagen = ImageOps.exif_transpose(original)
        imagen = imagen.convert("RGBA" if imagen.mode in ("RGBA", "LA", "P") else "RGB")
        imagen = ImageOps.fit(imagen, tam, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        salida = io.BytesIO()
        imagen.save(salida, format="WEBP", quality=85, method=4)
    return ContentFile(salida.getvalue(), name=f"{uuid.uuid4().hex}.webp")
