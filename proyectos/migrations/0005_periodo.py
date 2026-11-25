"""Spec 008, historia 2 · paso 1 de 3: modelo Periodo y un campo nuevo (todavía vacío) en Proyecto.

El campo de texto Proyecto.periodo se conserva hasta que la migración 0006 copie sus valores.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proyectos", "0004_codigos_faltantes"),
    ]

    operations = [
        migrations.CreateModel(
            name="Periodo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=60, unique=True, verbose_name="nombre")),
                ("slug", models.SlugField(editable=False, max_length=70, unique=True, verbose_name="dirección")),
                ("tipo", models.CharField(
                    choices=[("ordinario", "Ordinario"), ("intersemestral", "Intersemestral"), ("intensivo", "Intensivo"), ("otro", "Otro")],
                    default="ordinario", max_length=15, verbose_name="tipo",
                )),
                ("fecha_inicio", models.DateField(verbose_name="fecha de inicio")),
                ("fecha_fin", models.DateField(blank=True, null=True, verbose_name="fecha de fin")),
                ("abierto", models.BooleanField(
                    default=True, help_text="Si está abierto, los estudiantes pueden elegirlo al registrar un proyecto.",
                    verbose_name="abierto para entregas",
                )),
            ],
            options={
                "verbose_name": "periodo académico",
                "verbose_name_plural": "periodos académicos",
                "ordering": ["-fecha_inicio", "-id"],
            },
        ),
        migrations.AddField(
            model_name="proyecto",
            name="periodo_nuevo",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="proyectos.periodo",
            ),
        ),
    ]
