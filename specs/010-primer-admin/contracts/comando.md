# Contrato: comando `codigo_configuracion_inicial`

```text
python manage.py codigo_configuracion_inicial
```

Sin argumentos.

## Sin admin activo → código de salida 0

Escribe en **stdout** (en el log, nivel WARNING, solo queda un aviso sin el código, para no repetirlo en pantalla):

```text
==== VITRINA: CÓDIGO DE CONFIGURACIÓN INICIAL ====
Código: 7K4Q-M2XP-9WDA   (vence en 30 minutos)
Ábrelo en: https://sitio.ejemplo/configuracion-inicial/
===================================================
```

- `Ábrelo en:` usa `SITIO_URL` + `/configuracion-inicial/`; si `SITIO_URL` está vacío, solo la ruta.
- El código anterior (si había) deja de servir.

## Con admin activo → código de salida 1

`CommandError`: "Ya existe un administrador activo. La configuración inicial no está disponible."
No genera ni cambia nada.
