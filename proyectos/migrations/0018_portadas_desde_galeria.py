"""Spec 009, historia 7 (paso 2 de 2): la primera imagen de la galería pasa a ser la portada.

Antes, la cara del proyecto en la vitrina era su primera captura. Ahora es la imagen de portada; para
que ningún proyecto cambie de cara, se copia esa captura como portada (recortada a 16:9, 1200×675,
en webp con nombre aleatorio). La galería no se toca. Si un archivo no se puede leer (por ejemplo,
falta en el disco), ese proyecto queda con la portada de color.

Reversa: borra los archivos de portada y vacía el campo (al revertir el paso 1 el campo desaparece,
así que no queda nada que conservar). La galería sigue intacta.
"""

import io
import uuid

from django.core.files.base import ContentFile
from django.db import migrations

MEDIDA = (1200, 675)


def adelante(apps, schema_editor):
    from PIL import Image, ImageOps

    Proyecto = apps.get_model("proyectos", "Proyecto")
    Imagen = apps.get_model("proyectos", "Imagen")
    for proyecto in Proyecto.objects.filter(imagen_portada=""):
        primera = Imagen.objects.filter(proyecto=proyecto).order_by("orden", "id").first()
        if primera is None:
            continue
        try:
            with primera.archivo.open("rb") as archivo, Image.open(archivo) as original:
                imagen = ImageOps.exif_transpose(original).convert("RGB")
                imagen = ImageOps.fit(imagen, MEDIDA, method=Image.Resampling.LANCZOS)
                salida = io.BytesIO()
                imagen.save(salida, format="WEBP", quality=85)
        except (OSError, ValueError):
            continue
        proyecto.imagen_portada.save(f"{uuid.uuid4().hex}.webp", ContentFile(salida.getvalue()), save=False)
        Proyecto.objects.filter(pk=proyecto.pk).update(imagen_portada=proyecto.imagen_portada.name)


def atras(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    for proyecto in Proyecto.objects.exclude(imagen_portada=""):
        proyecto.imagen_portada.delete(save=False)
    Proyecto.objects.update(imagen_portada="")


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0017_portada_color_video")]

    operations = [migrations.RunPython(adelante, atras)]
