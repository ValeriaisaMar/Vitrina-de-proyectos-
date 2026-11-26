"""Spec 009, historia 2b: pasa a NFC el texto ya guardado de los comentarios (ver proyectos 0011)."""

import unicodedata

from django.db import migrations


def a_nfc(apps, schema_editor):
    Comentario = apps.get_model("comunidad", "Comentario")
    for comentario in Comentario.objects.only("pk", "texto").iterator():
        normal = unicodedata.normalize("NFC", comentario.texto)
        if normal != comentario.texto:
            Comentario.objects.filter(pk=comentario.pk).update(texto=normal)


class Migration(migrations.Migration):
    dependencies = [("comunidad", "0002_respuestas")]

    operations = [migrations.RunPython(a_nfc, migrations.RunPython.noop)]
