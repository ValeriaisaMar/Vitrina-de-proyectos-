"""Spec 009, historia 2b: pasa a NFC los nombres y apellidos ya guardados (ver proyectos 0011)."""

import unicodedata

from django.db import migrations


def a_nfc(apps, schema_editor):
    Usuario = apps.get_model("cuentas", "Usuario")
    for usuario in Usuario.objects.only("pk", "nombres", "apellidos").iterator():
        nombres = unicodedata.normalize("NFC", usuario.nombres)
        apellidos = unicodedata.normalize("NFC", usuario.apellidos)
        if (nombres, apellidos) != (usuario.nombres, usuario.apellidos):
            Usuario.objects.filter(pk=usuario.pk).update(nombres=nombres, apellidos=apellidos)


class Migration(migrations.Migration):
    dependencies = [("cuentas", "0005_configuracion_correo")]

    operations = [migrations.RunPython(a_nfc, migrations.RunPython.noop)]
