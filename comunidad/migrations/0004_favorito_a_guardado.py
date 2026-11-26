"""Spec 009, historia 2c: "Favoritos" pasa a llamarse "Guardados".

Había un solo modelo, así que no hay nada que unir: RenameModel cambia el nombre del modelo y de
la tabla y conserva todas las filas (nadie pierde lo que guardó). Es reversible.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("comunidad", "0003_texto_nfc"),
        ("proyectos", "0011_texto_nfc"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name="Favorito", new_name="Guardado"),
        migrations.AlterModelOptions(
            name="guardado",
            options={"ordering": ["-creado_en"], "verbose_name": "guardado", "verbose_name_plural": "guardados"},
        ),
        migrations.AlterField(
            model_name="guardado",
            name="proyecto",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="guardados", to="proyectos.proyecto"),
        ),
        migrations.AlterField(
            model_name="guardado",
            name="usuario",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="guardados", to=settings.AUTH_USER_MODEL),
        ),
    ]
