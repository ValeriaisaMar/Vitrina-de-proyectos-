"""Spec 008, historia 1 · paso 2 de 3: migración de datos.

Ida: cada usuario recibe como RolAsignado el rol que tiene hoy en Usuario.rol (desde su fecha de
registro) y ese rol queda como su último rol usado.
Vuelta: Usuario.rol se llena con el rol de mayor privilegio que tenga la persona.
"""

from django.db import migrations

JERARQUIA = ["estudiante", "profesor", "admin"]


def copiar_roles(apps, schema_editor):
    Usuario = apps.get_model("cuentas", "Usuario")
    RolAsignado = apps.get_model("cuentas", "RolAsignado")
    for usuario in Usuario.objects.all().only("pk", "rol", "fecha_registro"):
        rol = usuario.rol or "estudiante"
        RolAsignado.objects.get_or_create(usuario_id=usuario.pk, rol=rol, defaults={"asignado_en": usuario.fecha_registro})
        Usuario.objects.filter(pk=usuario.pk).update(ultimo_rol=rol)


def restaurar_rol(apps, schema_editor):
    Usuario = apps.get_model("cuentas", "Usuario")
    RolAsignado = apps.get_model("cuentas", "RolAsignado")
    for usuario in Usuario.objects.all().only("pk"):
        tiene = set(RolAsignado.objects.filter(usuario_id=usuario.pk).values_list("rol", flat=True))
        mayor = next((rol for rol in reversed(JERARQUIA) if rol in tiene), "estudiante")
        Usuario.objects.filter(pk=usuario.pk).update(rol=mayor)


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0002_roles_asignados"),
    ]

    operations = [
        migrations.RunPython(copiar_roles, restaurar_rol),
    ]
