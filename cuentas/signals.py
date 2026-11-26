"""Señales de la app cuentas (specs 009 y 010).

Una señal es una función que Django llama sola cuando pasa algo:
- cada vez que se guarda un Usuario nuevo se le crea su Perfil. Así toda cuenta tiene perfil, se
  cree desde el registro, desde la gestión de usuarios, con createsuperuser o en una prueba;
- cada vez que cambia un usuario o un rol se olvida si "hay un admin activo" (enlace de Entrar).
"""

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil_al_registrar(sender, instance, created, raw=False, **kwargs):
    if created and not raw:  # raw: al cargar fixtures no se crean objetos extra
        from cuentas.perfiles import crear_perfil

        crear_perfil(instance)


@receiver([post_save, post_delete], sender=settings.AUTH_USER_MODEL)
@receiver([post_save, post_delete], sender="cuentas.RolAsignado")
def olvidar_si_hay_admin(sender, raw=False, **kwargs):
    """Borra el valor guardado de "¿hay un admin activo?" (spec 010).

    Se llama al crear, guardar o borrar un usuario (activar o desactivar es guardar) y al dar o
    quitar un rol. Así el enlace "¿Instalación nueva?" de Entrar aparece o desaparece enseguida.
    """
    if not raw:
        from cuentas.configuracion_inicial import olvidar_cache

        olvidar_cache()
