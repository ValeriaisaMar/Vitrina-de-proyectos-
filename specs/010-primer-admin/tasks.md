# Tasks: Configuración inicial — crear el primer admin desde la app

**Input**: Design documents from `specs/010-primer-admin/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: obligatorios (constitución VIII y la spec pide pruebas por historia).

**Organization**: una fase por historia, en el orden de la spec. Al cerrar cada historia: suite
completa en verde, entrada en `APRENDIZAJE.md` y mensaje de commit sugerido (el equipo commitea).

## Format: `[ID] [P?] [Story] Description`

## Path Conventions

Proyecto Django en la raíz del repositorio: apps `cuentas/`, `vitrina/`, configuración en `config/`.

---

## Phase 1: Setup

- [X] T001 Anotar la línea base (482 pruebas en verde, rama `feat/010-primer-admin` desde `main` 3112faf) en `specs/010-primer-admin/tasks.md` (sección Notes)

---

## Phase 2: Foundational (bloquea todas las historias)

- [X] T002 Agregar el modelo `ConfiguracionInicial` (campos `ConfiguracionInicial.hash_codigo`, `ConfiguracionInicial.creado_en`, `ConfiguracionInicial.vence_en`, `ConfiguracionInicial.intentos_fallidos`, `ConfiguracionInicial.completada_en` según data-model.md) con método de clase `obtener()` (`get_or_create(pk=1)`) y el campo `CambioRol.motivo` (data-model.md) en `cuentas/models.py`
- [X] T003 Crear la migración reversible `cuentas/migrations/0009_configuracion_inicial.py` y comprobar `migrate cuentas 0008` / `migrate` de ida y vuelta
- [X] T004 Crear el servicio `cuentas/configuracion_inicial.py` con `hay_admin_activo()` (consulta directa: `is_active=True` + `RolAsignado` admin), `hay_admin_activo_en_cache()` (60 s, research R4), `olvidar_cache()` y el logger `cuentas.configuracion_inicial`

**Checkpoint**: modelo y función única de "admin activo" listos.

---

## Phase 3: User Story 1 — Código de un solo uso y logs por consola (P1) 🎯 MVP

**Goal**: generar, mostrar (terminal/log) y validar el código; logs por consola con `DEBUG=False`.

**Independent Test**: correr el comando dos veces y comprobar que solo vale el segundo código; abrir la
página sin código vigente y ver el bloque en el log.

### Tests for User Story 1

- [X] T005 [P] [US1] Pruebas del código en `cuentas/tests/test_configuracion_inicial.py`: formato y alfabeto, normalización (guiones, espacios, minúsculas), solo se guarda el hash, vence a los 30 min, un solo uso, 5 fallos lo invalidan y avisan (WARNING), generar desde la página no reemplaza uno vigente
- [X] T006 [P] [US1] Pruebas del comando en `cuentas/tests/test_configuracion_inicial.py`: imprime el bloque en stdout con `SITIO_URL` o solo la ruta, invalida el anterior, `CommandError` con admin activo sin cambiar nada
- [X] T007 [P] [US1] Pruebas de logging en `cuentas/tests/test_configuracion_inicial.py`: con `DEBUG=False` el logger emite el bloque (`assertLogs`), `settings.LOGGING` define el handler `consola` sin `require_debug_true`, `cuentas` en INFO sin propagar, `django` con `NIVEL_LOG_DJANGO`; la página GET (sin admin) escribe el bloque y su HTML no contiene el código

### Implementation for User Story 1

- [X] T008 [US1] En `cuentas/configuracion_inicial.py`: `ALFABETO`, `normalizar()`, `formatear()`, `_hash()`, `generar_codigo()` (reemplaza; contrato contracts/comando.md), `asegurar_codigo(url)` (solo si no hay vigente; escribe el bloque en el log), `bloque(codigo, url)`, `url_configuracion(request=None)` (usa `SITIO_URL`), `verificar_codigo(config, codigo)` con `hmac.compare_digest` y el conteo de fallos (data-model.md `ConfiguracionInicial.intentos_fallidos`)
- [X] T009 [US1] Comando `cuentas/management/__init__.py`, `cuentas/management/commands/__init__.py` y `cuentas/management/commands/codigo_configuracion_inicial.py` (stdout + log; `CommandError` si hay admin)
- [X] T010 [US1] `LOGGING` y `NIVEL_LOG_DJANGO` en `config/settings.py` (contracts/logging.md)
- [X] T011 [US1] Vista mínima `configuracion_inicial` (404 con admin; GET llama `asegurar_codigo`) en `cuentas/views.py`, ruta raíz en `config/urls.py` y plantilla `cuentas/templates/cuentas/configuracion_inicial.html` con la indicación de dónde está el código (sin el código)
- [X] T012 [US1] Revisar que ningún log escriba contraseñas, códigos introducidos ni la contraseña del correo (`cuentas/correos.py`, `cuentas/forms.py`, `cuentas/correo_envio.py`, `proyectos/correos.py`)
- [X] T013 [US1] `NIVEL_LOG_DJANGO` en `.env.example` y en la tabla de variables de `README.md`
- [X] T014 [US1] Entrada en `APRENDIZAJE.md` (hashing, `secrets`, comandos de gestión, logging)

**Checkpoint**: suite en verde; commit sugerido `feat: código de configuración inicial y logs por consola (spec 010, historia 1)`.

---

## Phase 4: User Story 2 — Enlace discreto en Entrar (P1)

**Goal**: el enlace aparece solo sin admin activo y desaparece al crearlo.

**Independent Test**: sin admin el enlace aparece en Entrar; al crear un admin desaparece en la
siguiente visita; no está en otras páginas.

### Tests for User Story 2

- [X] T015 [P] [US2] Pruebas en `cuentas/tests/test_configuracion_inicial.py`: enlace con y sin admin, desaparece tras dar el rol admin / activar una cuenta admin (caché invalidada), reaparece al desactivarla, no aparece en registro, portada ni explorar, Entrar no consulta "admin activo" en la segunda visita (`assertNumQueries`)

### Implementation for User Story 2

- [X] T016 [US2] Señales `post_save`/`post_delete` de `Usuario` y `RolAsignado` que llaman `olvidar_cache()` en `cuentas/signals.py`
- [X] T017 [US2] `entrar` pasa `mostrar_configuracion_inicial` en `cuentas/views.py`; enlace discreto (línea fina, ícono `settings`, texto pequeño suave, foco visible) en `cuentas/templates/cuentas/entrar.html`
- [X] T018 [US2] Comprobar que el ícono `settings` existe en `static/iconos/` (o agregarlo desde Tabler) y recompilar `static/css/app.css` si se usan clases nuevas
- [X] T019 [US2] Entrada en `APRENDIZAJE.md` (caché, señales, por qué vence en 60 s con varios procesos)

**Checkpoint**: suite en verde; commit sugerido `feat: enlace discreto a la configuración inicial en Entrar (spec 010, historia 2)`.

---

## Phase 5: User Story 3 — Asistente para crear el primer admin (P1)

**Goal**: crear o promover el primer admin de forma segura y entrar como admin.

**Independent Test**: base sin admin + código → cuenta nueva → panel del admin con "Listo…"; repetir
promoviendo un estudiante y verificar que conserva su rol.

### Tests for User Story 3

- [X] T020 [P] [US3] Pruebas en `cuentas/tests/test_primer_admin.py`: 404 con admin activo (GET y POST); sesión iniciada pide cerrarla; cuenta nueva (activa, solo rol admin, `asignado_por=None`, `CambioRol.motivo`, sin correo en `mail.outbox`); promover existente conserva roles y queda activa; contraseña incorrecta y correo inexistente dan el mismo mensaje que un código malo; código vencido/usado/erróneo; correo ya registrado en la pestaña nueva; contraseña débil; límite por IP; 5 fallos invalidan el código; dos llamadas al servicio crean un solo admin; sesión con rol activo admin y redirección al panel con mensaje y siguientes pasos; log INFO sin contraseña ni código; solo-admin sin perfil público; `createsuperuser` deja `CambioRol` con motivo, invalida el código y la caché

### Implementation for User Story 3

- [X] T021 [US3] `motivo` en `asignar_roles` y `dar_rol` de `cuentas/roles.py` (data-model.md `CambioRol.motivo`)
- [X] T022 [US3] Servicio `crear_primer_admin(codigo, opcion, datos)` con excepciones `ConfiguracionNoDisponible`, `DatosInvalidos` y `CorreoYaRegistrado` en `cuentas/configuracion_inicial.py` (`atomic` + `select_for_update` + re-chequeo, fallo anotado fuera del rollback, research R3, R7, R8; log INFO)
- [X] T023 [US3] `FormularioPrimerAdminNuevo` y `FormularioPrimerAdminExistente` en `cuentas/forms.py` (validadores de contraseña de Django; correo normalizado)
- [X] T024 [US3] Vista completa `configuracion_inicial` en `cuentas/views.py` (pestañas por `?opcion=`, límite por IP con `cuentas/limite.py`, login con `BACKEND`, `activar_rol(ADMIN)`, `messages.success`, `session["primeros_pasos"]`)
- [X] T025 [US3] Plantilla del asistente en `cuentas/templates/cuentas/configuracion_inicial.html`: sello, pasos 1 y 2, ayuda plegable `<details>` con los comandos (Docker, sin Docker, local), pestañas, "Volver a Entrar", aviso de sesión iniciada; responsive y modo oscuro
- [X] T026 [US3] Siguientes pasos en el panel del admin: `vitrina/views.py` (pop de `primeros_pasos`) y `vitrina/templates/vitrina/paneles/admin.html` (enlaces a `cuentas:correo_envio`, `proyectos:periodos`, `proyectos:planes`)
- [X] T027 [US3] `create_superuser` en `cuentas/managers.py`: `CambioRol` con motivo, invalidar el código y la caché
- [X] T028 [US3] Mostrar `motivo` en `CambioRolAdmin` (`cuentas/admin.py`) y en el historial de roles de `cuentas/templates/cuentas/usuario_editar.html`
- [X] T029 [US3] Entrada en `APRENDIZAJE.md` (transacciones, `select_for_update`, carreras, mensajes genéricos)

**Checkpoint**: suite en verde; commit sugerido `feat: asistente para crear el primer admin (spec 010, historia 3)`.

---

## Phase 6: User Story 4 — Qué pasa si se quedan sin admin (P2)

**Goal**: no se puede dejar la plataforma sin admin activo desde la app ni desde el panel de Django;
si pasa igual, la configuración vuelve con código nuevo.

**Independent Test**: con un solo admin, intentar desactivarlo/borrarlo/quitarle el rol en la app y en
`/admin/`; quitar el admin directo en la base y ver que el enlace vuelve y exige código.

### Tests for User Story 4

- [X] T030 [P] [US4] Pruebas en `cuentas/tests/test_ultimo_admin.py`: app — desactivar al último admin rechazado; `/admin/` — desactivar, borrar (vista y acción masiva) y quitar la fila admin en la tabla de roles rechazados; con dos admins sí se permite; sin admins (cambio directo con `update()`) el enlace reaparece tras vencer la caché y la página exige un código nuevo (el usado no sirve)

### Implementation for User Story 4

- [X] T031 [US4] Validación de desactivar al último admin en `FormularioGestionUsuario` y `UsuarioCambioForm` (`cuentas/forms.py`)
- [X] T032 [US4] `UsuarioAdmin` en `cuentas/admin.py`: `has_delete_permission` para el último admin, acción "borrar seleccionados" protegida, formset de roles que no deja quitar el admin al último admin
- [X] T033 [US4] Sección "Recuperar el acceso de administrador" en `README.md`
- [X] T034 [US4] Entrada en `APRENDIZAJE.md`

**Checkpoint**: suite en verde; commit sugerido `feat: el último admin no se puede desactivar ni borrar (spec 010, historia 4)`.

---

## Phase 7: Polish & Cross-Cutting

- [X] T035 Enmienda de la constitución a 3.1.0 (principios IV y V, excepción de la configuración inicial) en `.specify/memory/constitution.md` y `docs/sdd/constitucion.md`
- [X] T036 Traducciones: `locale/en/LC_MESSAGES/django.po` y compilar `django.mo`
- [X] T037 README: sección "Primer arranque" (servidor, respaldo por logs, `createsuperuser`, `NIVEL_LOG_DJANGO`)
- [X] T038 `python manage.py makemigrations --check --dry-run`, suite completa y `python manage.py check --deploy`-free sanity (`check`)
- [X] T039 Pruebas a mano 1–5 de quickstart.md con base temporal y `runserver` (DEBUG True y False)

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup → Foundational → US1 → US2 → US3 → US4 → Polish (orden pedido: una historia a la vez).

### User Story Dependencies

- US2 usa `hay_admin_activo_en_cache` (Foundational) y la ruta de US1.
- US3 usa el código de US1 y la invalidación de caché de US2.
- US4 usa `es_ultimo_admin` existente y el código de US1.

### Within Each User Story

- Pruebas primero (deben fallar), luego servicio → formularios → vista → plantilla.

### Parallel Opportunities

- Las tareas de prueba [P] de cada historia se pueden escribir en paralelo; el resto toca archivos
  compartidos (`cuentas/configuracion_inicial.py`, `cuentas/views.py`) y va en secuencia.

## Parallel Example: User Story 1

```text
T005, T006 y T007 (pruebas del código, del comando y del logging) en paralelo.
```

## Implementation Strategy

### MVP First

US1 sola ya permite generar y validar códigos; la instalación aún se completa con `createsuperuser`.

### Incremental Delivery

US1 → US2 → US3 (funcionalidad completa) → US4 (blindaje) → Polish.

## Notes

- Línea base: 482 pruebas en verde (2026-11-26), rama `feat/010-primer-admin` desde `main` (3112faf),
  con las correcciones locales del 26-nov incluidas por decisión del usuario.
- Sin commits automáticos: al cerrar cada historia se sugiere el mensaje.
- Final: 531 pruebas en verde; pruebas a mano 1–5 de quickstart.md correctas (2026-11-26).
