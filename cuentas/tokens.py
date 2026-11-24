"""Token del enlace de activación de cuenta.

Django ya trae un generador de tokens seguro para recuperar contraseñas
(PasswordResetTokenGenerator): firma los datos del usuario con la SECRET_KEY y le pone fecha,
así que vence solo (PASSWORD_RESET_TIMEOUT, 24 horas) sin guardar nada en la base de datos.

Aquí se reutiliza agregando "is_active" a los datos firmados: en cuanto la cuenta se activa, el
hash cambia y el mismo enlace deja de servir. Eso lo vuelve de un solo uso.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class GeneradorTokenActivacion(PasswordResetTokenGenerator):
    key_salt = "cuentas.tokens.GeneradorTokenActivacion"

    def _make_hash_value(self, usuario, timestamp):
        return f"{usuario.pk}{usuario.is_active}{usuario.email}{timestamp}"


token_activacion = GeneradorTokenActivacion()
