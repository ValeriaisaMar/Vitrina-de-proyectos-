"""Spec 009, historia 1 (paso 1 de 3): campos del período actual y del período de aprobación."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0007_periodo_como_relacion")]

    operations = [
        migrations.AddField(
            model_name="periodo",
            name="es_actual",
            field=models.BooleanField(
                default=False, help_text="El único período en el que los estudiantes pueden enviar proyectos.",
                verbose_name="período actual",
            ),
        ),
        migrations.AlterField(
            model_name="proyecto",
            name="periodo",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="proyectos", to="proyectos.periodo", verbose_name="periodo",
            ),
        ),
        migrations.AddField(
            model_name="proyecto",
            name="periodo_aprobacion",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="proyectos_aprobados", to="proyectos.periodo", verbose_name="periodo de aprobación",
            ),
        ),
    ]
