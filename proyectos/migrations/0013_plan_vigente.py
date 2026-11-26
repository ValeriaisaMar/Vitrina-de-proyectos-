"""Spec 009, historia 3 (paso 2 de 3): todas las asignaturas pasan al plan "Plan vigente".

Antes de asignarlas se fusionan las que solo se diferencian en mayúsculas o espacios ("Bases de
datos" y "bases  de datos"): se conserva la más antigua y sus proyectos pasan a ella. La lista de
fusiones se imprime al migrar. En la base del equipo no había ninguna (las asignaturas ya eran
una lista desde el módulo 003, no texto libre).

Reversa: las asignaturas quedan sin plan y se borra "Plan vigente" (las fusiones no se deshacen,
pero ningún proyecto se pierde: todos apuntan a una asignatura que existe).
"""

import datetime

from django.db import migrations

NOMBRE_PLAN = "Plan vigente"


def _clave(nombre):
    return " ".join(nombre.split()).casefold()


def adelante(apps, schema_editor):
    PlanEstudio = apps.get_model("proyectos", "PlanEstudio")
    Asignatura = apps.get_model("proyectos", "Asignatura")
    Proyecto = apps.get_model("proyectos", "Proyecto")

    conservadas = {}
    for asignatura in Asignatura.objects.order_by("pk"):
        clave = _clave(asignatura.nombre)
        if clave in conservadas:
            destino = conservadas[clave]
            Proyecto.objects.filter(asignatura_id=asignatura.pk).update(asignatura_id=destino.pk)
            print(f"\n  Asignatura fusionada: «{asignatura.nombre}» → «{destino.nombre}»", end="")
            asignatura.delete()
        else:
            conservadas[clave] = asignatura
            limpio = " ".join(asignatura.nombre.split())
            if limpio != asignatura.nombre:
                Asignatura.objects.filter(pk=asignatura.pk).update(nombre=limpio)

    plan, _ = PlanEstudio.objects.get_or_create(nombre=NOMBRE_PLAN, defaults={"anio": datetime.date.today().year})
    Asignatura.objects.filter(plan__isnull=True).update(plan=plan)


def atras(apps, schema_editor):
    Asignatura = apps.get_model("proyectos", "Asignatura")
    Asignatura.objects.update(plan=None)
    apps.get_model("proyectos", "PlanEstudio").objects.filter(nombre=NOMBRE_PLAN).delete()


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0012_planes_de_estudio")]

    operations = [migrations.RunPython(adelante, atras)]
