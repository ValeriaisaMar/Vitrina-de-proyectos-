"""Spec 009, historia 4 (paso 2 de 2): un perfil para cada usuario que ya existía.

Las cuentas nuevas reciben su perfil con una señal (cuentas/signals.py). Las que ya existían lo
reciben aquí, con un slug estable a partir del nombre. Quien ya había iniciado sesión no ve la
bienvenida "Completa tu perfil": esa invitación es para el primer inicio después de activar la cuenta.

Reversa: borra los perfiles (las cuentas no se tocan).
"""

from django.db import migrations
from django.utils.text import slugify


def _slug_unico(base, usados):
    base = slugify(base)[:80] or "persona"
    slug, n = base, 2
    while slug in usados:
        slug, n = f"{base}-{n}", n + 1
    usados.add(slug)
    return slug


def adelante(apps, schema_editor):
    Usuario = apps.get_model("cuentas", "Usuario")
    Perfil = apps.get_model("cuentas", "Perfil")
    usados = set(Perfil.objects.values_list("slug", flat=True))
    nuevos = [
        Perfil(
            usuario=usuario,
            slug=_slug_unico(f"{usuario.nombres} {usuario.apellidos}", usados),
            bienvenida_vista=usuario.last_login is not None,
        )
        for usuario in Usuario.objects.filter(perfil__isnull=True).order_by("pk")
    ]
    Perfil.objects.bulk_create(nuevos)


def atras(apps, schema_editor):
    apps.get_model("cuentas", "Perfil").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("cuentas", "0007_perfiles")]

    operations = [migrations.RunPython(adelante, atras)]
