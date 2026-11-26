# Contrato: logging

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"consola": {"class": "logging.StreamHandler", "formatter": "simple"}},  # stderr, sin filtro de DEBUG
    "loggers": {
        "cuentas": {"handlers": ["consola"], "level": "INFO", "propagate": False},
        "django": {"handlers": ["consola"], "level": NIVEL_LOG_DJANGO, "propagate": False},
    },
}
```

`NIVEL_LOG_DJANGO` (env, por defecto `INFO`): `DEBUG`, `INFO`, `WARNING`, `ERROR` o `CRITICAL`.

## Mensajes de `cuentas.configuracion_inicial`

| Nivel | Cuándo | Contenido |
|---|---|---|
| WARNING | código generado (página o comando) | el bloque del código |
| WARNING | 5 códigos fallidos | "Se invalidó el código … tras 5 intentos fallidos" (sin el código) |
| INFO | configuración completada | "Configuración inicial completada: admin <correo> (cuenta nueva/existente)" |

Nunca se registran: contraseñas, el código introducido, la contraseña de aplicación del correo.
