"""Spec 009, historia 1 (paso 2 de 3): datos.

- De los periodos abiertos, el más reciente (por fecha de inicio) queda como período actual.
- Los proyectos ya aprobados reciben su periodo como período de aprobación.

Reversa: los periodos actuales vuelven a quedar abiertos y se borra el período de aprobación
(el campo "abierto" vuelve a existir al deshacer el paso 3). No se pierde ningún proyecto.
"""

from django.db import migrations


def adelante(apps, schema_editor):
    Periodo = apps.get_model("proyectos", "Periodo")
    Proyecto = apps.get_model("proyectos", "Proyecto")
    mas_reciente = Periodo.objects.filter(abierto=True).order_by("-fecha_inicio", "-id").first()
    if mas_reciente is not None:
        Periodo.objects.filter(pk=mas_reciente.pk).update(es_actual=True)
    for proyecto in Proyecto.objects.filter(estado="aprobado", periodo__isnull=False, periodo_aprobacion__isnull=True):
        Proyecto.objects.filter(pk=proyecto.pk).update(periodo_aprobacion_id=proyecto.periodo_id)


def atras(apps, schema_editor):
    Periodo = apps.get_model("proyectos", "Periodo")
    Proyecto = apps.get_model("proyectos", "Proyecto")
    Periodo.objects.filter(es_actual=True).update(abierto=True, es_actual=False)
    Proyecto.objects.update(periodo_aprobacion=None)
    # Un borrador sin periodo no cabe en el esquema viejo (periodo obligatorio): se le da el más reciente
    reciente = Periodo.objects.order_by("-fecha_inicio", "-id").first()
    if reciente is not None:
        Proyecto.objects.filter(periodo__isnull=True).update(periodo=reciente)


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0008_periodo_actual")]

    operations = [migrations.RunPython(adelante, atras)]
