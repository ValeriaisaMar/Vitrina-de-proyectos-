"""Lectura de la configuración desde el archivo .env.

Todo lo que es secreto o cambia entre equipos (clave secreta, base de datos, correo) vive en
.env y se lee con las funciones de este módulo. Si falta una variable obligatoria, Django se
detiene con un mensaje que dice exactamente cuál falta, en vez de un error confuso más adelante.
"""

import os

from django.core.exceptions import ImproperlyConfigured

_VERDADEROS = {"1", "true", "t", "si", "sí", "yes", "y", "on"}


def variable(nombre, defecto=None, obligatoria=False):
    """Devuelve el valor de una variable de entorno como texto.

    Si es obligatoria y no existe (o está vacía), lanza ImproperlyConfigured con un mensaje
    que nombra la variable y dice dónde se configura.
    """
    valor = os.environ.get(nombre)
    if valor is None or valor.strip() == "":
        if obligatoria:
            raise ImproperlyConfigured(
                f"Falta la variable {nombre} en el archivo .env. "
                f"Copia .env.example como .env y complétala."
            )
        return defecto
    return valor.strip()


def booleano(nombre, defecto=False):
    """Lee una variable como verdadero o falso (acepta True, 1, sí, on…)."""
    valor = variable(nombre)
    if valor is None:
        return defecto
    return valor.lower() in _VERDADEROS


def lista(nombre, defecto=""):
    """Lee una variable con valores separados por comas y devuelve una lista sin vacíos."""
    valor = variable(nombre, defecto) or ""
    return [parte.strip() for parte in valor.split(",") if parte.strip()]
