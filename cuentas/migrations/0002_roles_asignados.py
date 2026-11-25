"""Spec 008, historia 1 · paso 1 de 3: tablas de roles asignados y del registro de cambios.

Todavía no se borra Usuario.rol: primero la migración 0003 copia cada rol actual a RolAsignado.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

ROLES = [("estudiante", "Estudiante"), ("profesor", "Profesor"), ("admin", "Admin")]


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="ultimo_rol",
            field=models.CharField(blank=True, choices=ROLES, max_length=12, verbose_name="último rol usado"),
        ),
        migrations.CreateModel(
            name="RolAsignado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rol", models.CharField(choices=ROLES, max_length=12, verbose_name="rol")),
                ("asignado_en", models.DateTimeField(default=django.utils.timezone.now, verbose_name="asignado en")),
                ("asignado_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="asignado por",
                )),
                ("usuario", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name="roles_asignados",
                    to=settings.AUTH_USER_MODEL, verbose_name="usuario",
                )),
            ],
            options={
                "verbose_name": "rol asignado",
                "verbose_name_plural": "roles asignados",
                "ordering": ["asignado_en", "id"],
                "constraints": [models.UniqueConstraint(fields=("usuario", "rol"), name="un_rol_por_persona")],
            },
        ),
        migrations.CreateModel(
            name="CambioRol",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rol", models.CharField(choices=ROLES, max_length=12, verbose_name="rol")),
                ("accion", models.CharField(choices=[("agregado", "agregado"), ("quitado", "quitado")], max_length=10, verbose_name="acción")),
                ("fecha", models.DateTimeField(default=django.utils.timezone.now, verbose_name="fecha")),
                ("hecho_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL, verbose_name="hecho por",
                )),
                ("usuario", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name="cambios_de_rol",
                    to=settings.AUTH_USER_MODEL, verbose_name="usuario",
                )),
            ],
            options={
                "verbose_name": "cambio de rol",
                "verbose_name_plural": "cambios de rol",
                "ordering": ["-fecha", "-id"],
            },
        ),
    ]
