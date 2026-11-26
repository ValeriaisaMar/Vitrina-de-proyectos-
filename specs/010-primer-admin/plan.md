# Implementation Plan: Configuración inicial — crear el primer admin desde la app

**Branch**: `feat/010-primer-admin` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-primer-admin/spec.md`

## Summary

Mientras no haya un admin activo, la Vitrina ofrece `/configuracion-inicial/`: un asistente que,
con un código de un solo uso (12 caracteres, 30 minutos, guardado solo como hash), crea una cuenta
admin nueva o promueve una existente. El código se obtiene con el comando
`codigo_configuracion_inicial` o, de respaldo, en los logs, que pasan a salir por consola también
con `DEBUG=False`. Se llega desde un enlace discreto en Entrar. Toda la lógica vive en el servicio
`cuentas/configuracion_inicial.py`; la creación es atómica con `select_for_update` sobre un registro
único `ConfiguracionInicial`. Se cierran los huecos que permitirían quedarse sin admin desde el panel
de Django (desactivar, borrar, quitar el rol en la tabla de roles).

## Technical Context

**Language/Version**: Python 3.12+ (el entorno local corre 3.15), Django 6.1

**Primary Dependencies**: las aprobadas (Django, psycopg, python-dotenv…). Nada nuevo: `secrets`,
`hashlib`, `hmac` y `logging` son de la biblioteca estándar.

**Storage**: PostgreSQL. Una tabla nueva (`cuentas_configuracioninicial`, una sola fila) y un campo
nuevo `CambioRol.motivo`. Caché `LocMemCache` existente.

**Testing**: `python manage.py test` (runner `config.pruebas.Ejecutor`, vacía la caché por prueba).
Línea base: 482 pruebas en verde.

**Target Platform**: servidor Linux (gunicorn, posiblemente varios procesos, con o sin Docker) y
desarrollo en Windows con `runserver`.

**Project Type**: aplicación web Django renderizada en el servidor.

**Performance Goals**: Entrar no agrega consultas en visitas repetidas (valor en caché).

**Constraints**: código nunca en claro en la base ni en HTML; logs sin datos sensibles; 360 px,
claro/oscuro, teclado; textos es/en; migraciones reversibles.

**Scale/Scope**: 1 modelo, 1 campo, 1 comando, 1 vista con 2 formularios, 1 plantilla, cambios en
Entrar, panel del admin, admin de Django, gestión de usuarios, `managers.py`, `settings.py`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Nota |
|---|---|---|
| I. Tecnología / apps | ✅ | Todo en `cuentas`; `config/urls.py` monta la ruta raíz. El panel (vitrina) solo lee una clave de sesión del servicio de cuentas, no importa vistas. Docker solo se menciona en el README. |
| II. Consultas seguras | ✅ | Solo ORM. |
| III. Entradas no confiables | ✅ | Formularios de Django, CSRF, escapado automático. |
| IV. Autenticación segura | ⚠️ → enmienda | La cuenta del primer admin nace activa sin enlace. Excepción acotada (solo sin admin activo y con código del servidor). Enmienda 3.1.0. Validadores de contraseña y límite por IP se mantienen. |
| V. Permisos por rol | ⚠️ → enmienda | El primer admin recibe el rol sin otro admin. Misma excepción en la enmienda 3.1.0. Permisos en el servidor: 404 con admin activo, comprobado dentro de la transacción. |
| VI–VII | ✅ | No aplica. |
| VIII. Pruebas | ✅ | Pruebas por historia en `cuentas/tests/`. |
| IX. Código entendible | ✅ | Vista por función; lógica en el servicio; docstrings; `APRENDIZAJE.md` por historia. |
| X. Interfaz | ✅ | Hereda `base_acceso.html`, `{% icono %}`, Tailwind compilado. |
| XI. Idioma | ✅ | `.po` editado y `.mo` compilado (sin gettext en Windows: script propio). |
| XII. Dependencias | ✅ | Ninguna nueva. |
| XIII. Secretos | ✅ | `NIVEL_LOG_DJANGO` en `.env.example`; no se lee ni toca `.env`. |
| XIV. Flujo | ✅ | Rama `feat/010-primer-admin`; commits los hace el equipo. |

**Gate**: pasa con la enmienda justificada en Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/010-primer-admin/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── comando.md          # salida y códigos de salida del comando
│   ├── pagina.md           # GET/POST /configuracion-inicial/ y enlace en Entrar
│   └── logging.md          # configuración LOGGING y mensajes
└── tasks.md                # /speckit-tasks
```

### Source Code (repository root)

```text
config/
├── settings.py                         # LOGGING, NIVEL_LOG_DJANGO
└── urls.py                             # path("configuracion-inicial/", …)
cuentas/
├── configuracion_inicial.py            # NUEVO: servicio (hay_admin_activo, código, crear_primer_admin)
├── models.py                           # ConfiguracionInicial; CambioRol.motivo
├── migrations/0009_configuracion_inicial.py
├── management/commands/codigo_configuracion_inicial.py   # NUEVO
├── forms.py                            # FormularioPrimerAdminNuevo/Existente; último admin al desactivar
├── views.py                            # vista configuracion_inicial; entrar pasa el indicador
├── roles.py                            # motivo en asignar_roles/dar_rol
├── managers.py                         # create_superuser deja CambioRol e invalida código/caché
├── signals.py                          # invalidar la caché del indicador
├── admin.py                            # último admin: desactivar, borrar, quitar rol; motivo visible
├── templates/cuentas/configuracion_inicial.html          # NUEVO
├── templates/cuentas/entrar.html       # enlace discreto
└── tests/test_configuracion_inicial.py, test_primer_admin.py, test_ultimo_admin.py  # NUEVOS
vitrina/
├── views.py                            # panel admin: siguientes pasos tras la configuración
└── templates/vitrina/paneles/admin.html
locale/en/LC_MESSAGES/django.po/.mo
.specify/memory/constitution.md, docs/sdd/constitucion.md   # enmienda 3.1.0
README.md, .env.example, APRENDIZAJE.md
```

**Structure Decision**: aplicación Django existente; todo en la app `cuentas` siguiendo el patrón de
servicios (`roles.py`, `correo_envio.py`).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Cuenta activa sin enlace de activación (IV) | Quien crea el primer admin demostró acceso al servidor con el código; puede que el correo aún no esté configurado, así que el enlace nunca llegaría. | Mandar el enlace: sin correo configurado (caso normal en un servidor nuevo) el admin no podría activarse nunca. |
| Rol admin sin un admin que lo dé (V) | No existe ningún admin que pueda darlo. | `createsuperuser`: es justo lo que la spec quiere evitar; se mantiene como alternativa. |
