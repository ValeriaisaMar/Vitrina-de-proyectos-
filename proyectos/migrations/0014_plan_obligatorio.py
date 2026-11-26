"""Spec 009, historia 3 (paso 3 de 3): toda asignatura pertenece a un plan y su nombre es único en él."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0013_plan_vigente")]

    operations = [
        migrations.AlterField(
            model_name="asignatura",
            name="plan",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="asignaturas",
                to="proyectos.planestudio", verbose_name="plan de estudios",
            ),
        ),
        migrations.AddConstraint(
            model_name="asignatura",
            constraint=models.UniqueConstraint(fields=("plan", "nombre"), name="asignatura_unica_por_plan"),
        ),
    ]
