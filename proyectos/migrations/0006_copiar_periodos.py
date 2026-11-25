"""Spec 008, historia 2 · paso 2 de 3: migración de datos de periodos.

Ida:
- Por cada valor distinto de Proyecto.periodo ("2025-2", "2026-1"…) se crea un Periodo ordinario
  con ese nombre. Fecha de inicio inferida: "-1" → 1 de enero, "-2" → 1 de julio.
- Queda abierto si es del año actual o posterior; los anteriores quedan cerrados.
- Se crea además el periodo del semestre actual si no existía, para que los estudiantes tengan
  al menos uno abierto en una instalación nueva.
- Cada proyecto apunta a su Periodo.
Vuelta: el texto del periodo se recupera del nombre (recortado a 6 caracteres).
"""

import datetime

from django.db import migrations
from django.utils import timezone
from django.utils.text import slugify


def _fecha_inicio(nombre):
    try:
        anio, semestre = nombre.split("-")
        return datetime.date(int(anio), 7 if semestre == "2" else 1, 1)
    except (ValueError, TypeError):
        return datetime.date(timezone.localdate().year, 1, 1)


def _periodo(Periodo, nombre, hoy):
    inicio = _fecha_inicio(nombre)
    periodo, _creado = Periodo.objects.get_or_create(
        nombre=nombre,
        defaults={"slug": slugify(nombre) or "periodo", "tipo": "ordinario", "fecha_inicio": inicio, "abierto": inicio.year >= hoy.year},
    )
    return periodo


def copiar_periodos(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    Periodo = apps.get_model("proyectos", "Periodo")
    hoy = timezone.localdate()
    for nombre in Proyecto.objects.values_list("periodo", flat=True).distinct():
        periodo = _periodo(Periodo, nombre or "2026-1", hoy)
        Proyecto.objects.filter(periodo=nombre).update(periodo_nuevo=periodo)
    _periodo(Periodo, f"{hoy.year}-{1 if hoy.month < 7 else 2}", hoy)


def restaurar_texto(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    for proyecto in Proyecto.objects.select_related("periodo_nuevo").exclude(periodo_nuevo=None):
        Proyecto.objects.filter(pk=proyecto.pk).update(periodo=proyecto.periodo_nuevo.nombre[:6])


class Migration(migrations.Migration):

    dependencies = [
        ("proyectos", "0005_periodo"),
    ]

    operations = [
        migrations.RunPython(copiar_periodos, restaurar_texto),
    ]
