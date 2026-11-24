# Tasks: Cuentas y autenticación

**Input**: [spec.md](spec.md) y [plan.md](plan.md). Cada tarea deja su entrada en `APRENDIZAJE.md`.

## Fase 1: Base

- [x] T001 `cuentas/tokens.py`: generador de token de activación de un solo uso
- [x] T002 `cuentas/limite.py`: bloqueo por intentos fallidos (5 en 15 minutos)
- [x] T003 `cuentas/decoradores.py`: `@rol_requerido` y `templates/403.html`
- [x] T004 `cuentas/urls.py` con `app_name = "cuentas"`; `config/urls.py` y `LOGIN_URL`

## Fase 2: Historia 1 — Registro y activación (P1)

- [x] T005 [US1] `FormularioRegistro` (nombres, apellidos, correo único, contraseñas)
- [x] T006 [US1] `cuentas/correos.py` y plantillas del correo de activación (texto y HTML)
- [x] T007 [US1] Vistas `registro`, `revisa_correo`, `activar` y `reenviar_activacion` con sus plantillas
- [x] T008 [US1] Pruebas en `cuentas/tests/test_registro.py`

## Fase 3: Historia 2 — Entrar y salir (P1)

- [x] T009 [US2] `FormularioEntrar` con "Mantener la sesión iniciada" y aviso de cuenta inactiva
- [x] T010 [US2] Vistas `entrar` (con límite de intentos y `next` seguro) y `salir` (POST)
- [x] T011 [US2] Pruebas en `cuentas/tests/test_entrar.py`

## Fase 4: Historia 3 — Recuperar la contraseña (P1)

- [x] T012 [US3] Rutas con las vistas de Django y plantillas propias (pantallas y correo)
- [x] T013 [US3] Pruebas en `cuentas/tests/test_recuperacion.py`

## Fase 5: Historia 4 — Perfil (P2)

- [x] T014 [US4] `FormularioPerfil`, vista `perfil` y cambio de contraseña
- [x] T015 [US4] Pruebas en `cuentas/tests/test_perfil.py`

## Fase 6: Historia 5 — Permisos por rol (P1)

- [x] T016 [US5] Pruebas de `@rol_requerido` y de la página 403 en `cuentas/tests/test_permisos.py`

## Fase 7: Cierre

- [x] T017 Encabezado, pie y portada con los enlaces nuevos
- [x] T018 Traducciones al inglés
- [x] T019 Compilar Tailwind, revisión visual y `python manage.py test` en verde
- [x] T020 `APRENDIZAJE.md` y entrega
