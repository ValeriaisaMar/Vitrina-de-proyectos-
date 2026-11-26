"""Spec 009, historia 1 (paso 3 de 3): se quita "abierto" y se garantiza un solo período actual."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("proyectos", "0009_copiar_periodo_actual")]

    operations = [
        migrations.RemoveField(model_name="periodo", name="abierto"),
        migrations.AddConstraint(
            model_name="periodo",
            constraint=models.UniqueConstraint(
                condition=models.Q(("es_actual", True)), fields=("es_actual",), name="un_solo_periodo_actual",
            ),
        ),
    ]
