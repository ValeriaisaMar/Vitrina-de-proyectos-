"""Spec 008, historia 2 · paso 3 de 3: se quita el periodo de texto y el campo nuevo toma su nombre.

Al revertir: el campo vuelve a llamarse periodo_nuevo, reaparece el texto (vacío) y la
migración 0006 lo completa desde el nombre de cada Periodo.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proyectos", "0006_copiar_periodos"),
    ]

    operations = [
        # Antes de quitar el texto se le da un valor por defecto: así, al revertir, la columna se puede
        # volver a crear en una tabla que ya tiene filas (luego la 0006 la llena con el nombre).
        migrations.AlterField(
            model_name="proyecto", name="periodo",
            field=models.CharField(blank=True, default="", max_length=6, verbose_name="periodo"),
        ),
        migrations.RemoveField(model_name="proyecto", name="periodo"),
        migrations.RenameField(model_name="proyecto", old_name="periodo_nuevo", new_name="periodo"),
        migrations.AlterField(
            model_name="proyecto",
            name="periodo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="proyectos",
                to="proyectos.periodo", verbose_name="periodo",
            ),
        ),
    ]
