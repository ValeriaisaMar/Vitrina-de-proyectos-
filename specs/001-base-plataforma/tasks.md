# Tasks: Base de la plataforma

**Input**: [spec.md](spec.md) y [plan.md](plan.md)

Formato: `[ID] [P?] [Historia] Descripción`. `[P]` = se puede hacer en paralelo con otras `[P]`.
Cada tarea terminada deja una entrada en `APRENDIZAJE.md`.

## Fase 1: Preparación

- [x] T001 Pasar `requirements.txt` a UTF-8 con las dependencias aprobadas y versiones fijas
- [x] T002 [P] Crear `.env.example` y ampliar `.gitignore` (ejecutable de Tailwind, `media/`, `staticfiles/`)
- [x] T003 [P] Crear las apps `cuentas`, `proyectos` y `comunidad` con su paquete `tests/`

## Fase 2: Base que bloquea todo lo demás

- [x] T004 [US1] Crear `config/entorno.py` con `variable()` y sus pruebas en `cuentas/tests/test_entorno.py`
- [x] T005 [US1] Reescribir `config/settings.py`: `.env`, PostgreSQL, apps, idiomas, plantillas, estáticos, `MAILERS`, seguridad
- [x] T006 [US1] Crear `Rol`, `UsuarioManager` y `Usuario` en `cuentas/`; `AUTH_USER_MODEL = "cuentas.Usuario"`
- [x] T007 [US1] Generar `cuentas/migrations/0001_initial.py` y migrar contra PostgreSQL vacío
- [x] T008 [US1] Registrar `UsuarioAdmin` con búsqueda por correo y nombre y edición del rol
- [x] T009 [US1] Pruebas de usuario y admin en `cuentas/tests/`

## Fase 3: Historia 2 — Portada con la identidad UTEQ (P1)

- [x] T010 [US2] Copiar Unbounded y Archivo (woff2 + licencia) a `static/fonts/`
- [x] T011 [US2] Escribir `static/src/entrada.css`: fuentes, tokens claro/oscuro, colores de estado, componentes y animaciones con `prefers-reduced-motion`
- [x] T012 [US2] Crear `templates/base.html` y los parciales (encabezado con menú `<details>`, pie, mensajes, enlace "Saltar al contenido")
- [x] T013 [P] [US2] Crear los componentes `boton`, `campo`, `aviso` e `insignia_estado`
- [x] T014 [US2] Crear `config/contexto.py` (logo opcional) y registrarlo
- [x] T015 [US2] Reescribir `vitrina/views.py`, `urls.py` e `inicio.html` (portada animada, Cómo funciona, invitación) y la página `proximamente.html`
- [x] T016 [US2] Plantilla `registration/login.html` temporal; eliminar el registro viejo y las plantillas y CSS anteriores
- [x] T017 [US2] Compilar `static/css/app.css` con Tailwind standalone (`--minify`)
- [x] T018 [US2] Pruebas de la portada en `vitrina/tests/test_paginas.py`

## Fase 4: Historia 3 — Español e inglés (P1)

- [x] T019 [US3] Activar `LocaleMiddleware`, `LANGUAGES`, `LOCALE_PATHS` y la ruta `i18n/`
- [x] T020 [US3] Selector de idioma por POST con `aria-pressed` en `parciales/selector_idioma.html`
- [x] T021 [US3] Traducir todos los textos en `locale/en/LC_MESSAGES/django.po` y compilar `django.mo`
- [x] T022 [US3] Pruebas en `vitrina/tests/test_idioma.py`

## Fase 5: Historia 4 — Modo claro y oscuro (P2)

- [x] T023 [US4] Script en el `<head>` que aplica el tema antes de pintar
- [x] T024 [US4] `static/js/tema.js`: botón de tema con etiqueta accesible y memoria en el navegador

## Fase 6: Historia 5 — Páginas de error (P3)

- [x] T025 [US5] Crear `templates/404.html` y `templates/500.html`
- [x] T026 [US5] Pruebas en `vitrina/tests/test_errores.py`

## Fase 7: Cierre

- [x] T027 Ejecutar `python manage.py test` completo en verde
- [x] T028 Revisión visual en 360, 768, 1280 y 1920 px, en ambos temas y ambos idiomas
- [x] T029 Completar `APRENDIZAJE.md` y preparar la entrega

## Lista de revisión manual (T028)

- [ ] 360 px: sin desplazamiento horizontal; el menú se abre y se cierra
- [ ] 768 px y 1280 px: encabezado en una sola fila; tarjetas de "Cómo funciona" alineadas
- [ ] 1920 px: el contenido queda centrado con ancho máximo
- [ ] Modo oscuro: todo el texto se lee; al recargar no hay destello
- [ ] Inglés: ningún texto de interfaz en español
- [ ] Teclado: el primer Tab muestra "Saltar al contenido" y el foco siempre se ve
- [ ] Sistema con "reducir movimiento": la portada no se anima
