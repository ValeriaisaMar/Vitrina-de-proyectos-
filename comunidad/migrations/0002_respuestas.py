# Spec 008, historia 4: los autores responden comentarios (un solo nivel).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comunidad', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='comentario',
            name='respuesta_a',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='respuestas', to='comunidad.comentario', verbose_name='en respuesta a'),
        ),
    ]
