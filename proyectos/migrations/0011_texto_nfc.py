"""Spec 009, historia 2b: pasa a NFC (letras compuestas) el texto ya guardado de los proyectos.

Un título copiado de macOS o de un PDF puede venir en NFD («n» + tilde suelta), que el certificado
PDF no sabe componer. El contenido no cambia, solo la forma de guardar cada letra. El historial de
estados no se toca: es inmutable (constitución, VII). La reversa no hace nada (NFC y NFD se ven igual).
"""

import unicodedata

from django.db import migrations

CAMPOS = ("titulo", "resumen", "descripcion")


def a_nfc(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    for proyecto in Proyecto.objects.only("pk", *CAMPOS).iterator():
        cambios = {c: unicodedata.normalize("NFC", getattr(proyecto, c)) for c in CAMPOS}
        if any(cambios[c] != getattr(proyecto, c) for c in CAMPOS):
            Proyecto.objects.filter(pk=proyecto.pk).update(**cambios)


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0010_quitar_abierto")]

    operations = [migrations.RunPython(a_nfc, migrations.RunPython.noop)]
