"""Spec 009, historia 3 (paso 1 de 3): planes de estudio y código de las asignaturas."""

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0011_texto_nfc")]

    operations = [
        migrations.CreateModel(
            name="PlanEstudio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=80, unique=True, verbose_name="nombre")),
                ("anio", models.PositiveSmallIntegerField(
                    validators=[django.core.validators.MinValueValidator(1990), django.core.validators.MaxValueValidator(2100)],
                    verbose_name="año",
                )),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
            ],
            options={"verbose_name": "plan de estudios", "verbose_name_plural": "planes de estudio", "ordering": ["-anio", "nombre"]},
        ),
        migrations.AddField(
            model_name="asignatura",
            name="plan",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT, related_name="asignaturas",
                to="proyectos.planestudio", verbose_name="plan de estudios",
            ),
        ),
        migrations.AddField(
            model_name="asignatura",
            name="codigo",
            field=models.CharField(blank=True, max_length=20, verbose_name="código"),
        ),
        migrations.AlterField(
            model_name="asignatura",
            name="nombre",
            field=models.CharField(max_length=120, verbose_name="nombre"),
        ),
    ]
