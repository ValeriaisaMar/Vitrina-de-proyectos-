"""Configuración de la app cuentas: Usuario, registro, activación, inicio de sesión, recuperación y roles."""

from django.apps import AppConfig


class CuentasConfig(AppConfig):
    name = "cuentas"
    verbose_name = "Cuentas"

    def ready(self):
        """Conecta las señales (cuentas/signals.py) cuando Django termina de cargar las apps."""
        from cuentas import signals  # noqa: F401
