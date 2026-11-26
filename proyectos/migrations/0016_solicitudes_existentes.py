"""Spec 009, historia 5 (paso 2 de 2): los proyectos que ya estaban en revisión.

- En revisión con un profesor: conservan ese revisor y reciben una solicitud aceptada a su nombre,
  para que el historial de solicitudes cuente lo que pasó.
- Enviados sin revisor: no hace falta tocarlos. Sin solicitud pendiente quedan "Por asignar
  revisor" y su creador ve un aviso en el panel para elegir (no se manda ningún correo masivo).
Los eventos existentes quedan con la acción "estado" (el valor por defecto del campo nuevo).

Reversa: borra las solicitudes creadas aquí (las marcadas como creadas por la migración).
"""

from django.db import migrations
from django.db.models import Max

MARCA = "Creada por la migración 0016 (spec 009)."


def adelante(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    SolicitudRevision = apps.get_model("proyectos", "SolicitudRevision")
    en_revision = (
        Proyecto.objects.filter(estado="en_revision", revisor__isnull=False)
        .annotate(tomado_en=Max("eventos__creado_en"))
    )
    for proyecto in en_revision:
        if not SolicitudRevision.objects.filter(proyecto=proyecto, profesor_id=proyecto.revisor_id, estado="aceptada").exists():
            SolicitudRevision.objects.create(
                proyecto=proyecto, profesor_id=proyecto.revisor_id, estado="aceptada",
                respondida_en=proyecto.tomado_en, mensaje=MARCA,
            )


def atras(apps, schema_editor):
    apps.get_model("proyectos", "SolicitudRevision").objects.filter(mensaje=MARCA).delete()


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0015_solicitudes_revision")]

    operations = [migrations.RunPython(adelante, atras)]
