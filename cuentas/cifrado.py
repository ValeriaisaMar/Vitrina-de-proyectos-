"""Cifrado de la contraseña de aplicación del correo (spec 008, historia 3).

Se usa Fernet, de la librería cryptography: cifrado simétrico (la misma clave cifra y descifra)
que además detecta si el texto cifrado fue alterado. La clave vive en la variable de entorno
CLAVE_CIFRADO del .env, nunca en la base de datos: quien robe solo la base no puede leer la
contraseña.

Generar una clave:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ClaveIlegible(Exception):
    """La contraseña guardada no se puede descifrar (por ejemplo, cambió CLAVE_CIFRADO)."""


def _fernet():
    clave = getattr(settings, "CLAVE_CIFRADO", "") or ""
    if not clave:
        raise ImproperlyConfigured(
            "Falta la variable CLAVE_CIFRADO en el archivo .env. Genera una con: "
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    try:
        return Fernet(clave.encode() if isinstance(clave, str) else clave)
    except (ValueError, TypeError) as error:
        raise ImproperlyConfigured("CLAVE_CIFRADO no es una clave Fernet válida (44 caracteres en base64).") from error


def hay_clave():
    """True si CLAVE_CIFRADO está configurada y es válida."""
    try:
        _fernet()
    except ImproperlyConfigured:
        return False
    return True


def cifrar(texto):
    return _fernet().encrypt(texto.encode("utf-8")).decode("ascii")


def descifrar(cifrado):
    try:
        return _fernet().decrypt(cifrado.encode("ascii")).decode("utf-8")
    except InvalidToken as error:
        raise ClaveIlegible("No se pudo descifrar la contraseña guardada.") from error
