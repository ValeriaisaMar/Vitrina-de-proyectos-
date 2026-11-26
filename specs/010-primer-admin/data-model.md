# Data Model: Configuración inicial (spec 010)

Migración nueva `cuentas/migrations/0009_configuracion_inicial.py` (reversible, sin tocar datos).

## ConfiguracionInicial (nuevo, una sola fila `pk=1`)

| Campo | Tipo | Notas |
|---|---|---|
| `hash_codigo` | CharField(64), blank | SHA-256 hex del código vigente; vacío = no hay código vigente |
| `creado_en` | DateTimeField, null | cuándo se generó el código vigente |
| `vence_en` | DateTimeField, null | `creado_en + 30 min` |
| `intentos_fallidos` | PositiveSmallIntegerField, default 0 | con el código vigente; a los 5 se borra el código |
| `completada_en` | DateTimeField, null | última vez que se creó el primer admin (histórico) |

**Reglas**

- Código vigente ⇔ `hash_codigo != ""` y `vence_en > ahora`.
- Generar: guarda hash, fechas y `intentos_fallidos = 0` (reemplaza el anterior).
- Usar con éxito o completar: `hash_codigo = ""`, `completada_en = ahora`.
- 5 fallos: `hash_codigo = ""` y WARNING en el log.
- La disponibilidad de la página NO depende de `completada_en` sino de `hay_admin_activo()`.

```text
sin código ──generar──▶ vigente ──usar bien──▶ sin código (completada)
                         │  ├──vence (30 min)──▶ sin código
                         │  ├──5 fallos────────▶ sin código
                         └──generar (comando)─▶ vigente (nuevo)
```

## CambioRol (existente) — campo nuevo

| Campo | Tipo | Notas |
|---|---|---|
| `motivo` | CharField(120), blank, default "" | "Configuración inicial" para el primer admin y `createsuperuser` |

## Usuario, RolAsignado (existentes, sin cambios de esquema)

- Primer admin: `is_active=True`; `RolAsignado(rol="admin", asignado_por=None)`.
- **Admin activo**: `Usuario.is_active=True` y existe `RolAsignado(rol="admin")`.
