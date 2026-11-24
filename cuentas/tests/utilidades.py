"""Ayudas compartidas por las pruebas de cuentas."""

import re

from django.contrib.auth import get_user_model

Usuario = get_user_model()
CLAVE = "una-clave-segura-123"


def crear_usuario(email="ana@correo.com", activo=True, rol="estudiante", **extra):
    datos = {"nombres": "Ana", "apellidos": "Pérez", "rol": rol, "is_active": activo, **extra}
    return Usuario.objects.create_user(email=email, password=CLAVE, **datos)


def enlace_en_correo(correo):
    """Saca la ruta (sin dominio) del primer enlace http del cuerpo de texto de un correo."""
    coincidencia = re.search(r"https?://[^/\s]+(/\S+)", correo.body)
    assert coincidencia, "El correo no trae ningún enlace"
    return coincidencia.group(1)
