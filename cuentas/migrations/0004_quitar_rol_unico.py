"""Spec 008, historia 1 · paso 3 de 3: se elimina Usuario.rol (los roles ya están en RolAsignado).

Al revertir, el campo vuelve con "estudiante" por defecto y la migración 0003 lo completa.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0003_copiar_roles"),
    ]

    operations = [
        migrations.RemoveField(model_name="usuario", name="rol"),
    ]
