"""Da su código VP-AAAA-NNNN a los proyectos aprobados que no lo tienen.

En el módulo 003, antes de existir la revisión, se podía aprobar un proyecto a mano desde /admin/.
Esos proyectos quedaron aprobados sin código ni fecha de aprobación, y por eso no tenían QR ni
certificado. Esta migración los completa con el mismo contador por año que usa servicios.py.
Si no hay proyectos así, no hace nada.
"""

from django.db import migrations
from django.utils import timezone


def completar_codigos(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    Consecutivo = apps.get_model("proyectos", "Consecutivo")
    pendientes = Proyecto.objects.filter(estado="aprobado", codigo__isnull=True).order_by("actualizado_en", "id")
    for proyecto in pendientes:
        if proyecto.aprobado_en is None:
            proyecto.aprobado_en = proyecto.actualizado_en
        anio = timezone.localtime(proyecto.aprobado_en).year
        contador, _ = Consecutivo.objects.get_or_create(anio=anio)
        contador.ultimo += 1
        contador.save(update_fields=["ultimo"])
        proyecto.codigo = f"VP-{anio}-{contador.ultimo:04d}"
        proyecto.save(update_fields=["aprobado_en", "codigo"])


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0003_eventoestado_consecutivo")]

    # Al deshacerla no se quitan los códigos: un código entregado no debe cambiar nunca.
    operations = [migrations.RunPython(completar_codigos, migrations.RunPython.noop)]
