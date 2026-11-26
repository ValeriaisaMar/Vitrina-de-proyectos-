"""Señales de la app cuentas (spec 009).

Una señal es una función que Django llama sola cuando pasa algo; aquí, cada vez que se guarda un
Usuario nuevo se le crea su Perfil. Así toda cuenta tiene perfil, se cree desde el registro, desde
la gestión de usuarios, con createsuperuser o en una prueba.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil_al_registrar(sender, instance, created, raw=False, **kwargs):
    if created and not raw:  # raw: al cargar fixtures no se crean objetos extra
        from cuentas.perfiles import crear_perfil

        crear_perfil(instance)
