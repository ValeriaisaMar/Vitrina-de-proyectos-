# Tasks: Perfiles, profesor revisor elegido, período actual y navegación

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/rutas.md](contracts/rutas.md)
**Tests**: pedidos por el documento de la 009 y por la constitución (VIII): cada historia trae sus pruebas.
**Commits**: los hace el equipo; al cerrar cada historia se propone el mensaje (Conventional Commits).

## Phase 1: Setup

- [X] T001 Línea base: correr la suite completa y anotar el resultado (357 pruebas OK, 2026-11-25) en APRENDIZAJE.md
- [X] T002 Enmienda de la constitución a 3.0.0 (III 5 MB foto/portada; V y VII revisor elegido y solo el asignado decide) en .specify/memory/constitution.md y docs/sdd/constitucion.md

## Phase 2: Foundational

- [X] T003 [P] Copiar los SVG de Tabler Icons (MIT) y de GitHub, LinkedIn y ORCID (Simple Icons, CC0) con sus licencias en static/iconos/ y static/iconos/LICENCIAS.txt
- [X] T004 Etiqueta `{% icono %}` (aria-hidden por defecto, `tam`, `clase`, `etiqueta`) registrada como builtin en vitrina/templatetags/iconos.py y config/settings.py, con pruebas en vitrina/tests/test_iconos.py
- [X] T005 [P] Utilidad de imágenes (Pillow, jpg/png/webp, ≤ 5 MB, EXIF, recorte, webp, uuid) en config/imagenes.py con pruebas en vitrina/tests/test_imagenes.py

## Phase 3: User Story 1 — Un solo período actual (P1)

**Goal**: el admin designa un período actual; el proyecto lo toma al enviarse y guarda el de aprobación.
**Independent Test**: marcar actual, enviar, aprobar y ver el período en la verificación.

- [X] T006 [US1] Pruebas: un solo actual, marcar otro desmarca, enviar sin actual, período al enviar, período de aprobación en verificación y PDF, pie con el período, en proyectos/tests/test_periodo_actual.py (y ajustar proyectos/tests/test_periodos.py)
- [X] T007 [US1] Modelos: data-model.md `Periodo.es_actual` (restricción condicional), `Proyecto.periodo` nulo, `Proyecto.periodo_aprobacion` en proyectos/models.py
- [X] T008 [US1] Migraciones 0008 (campos), 0009 (datos: abierto más reciente → actual; aprobados → periodo_aprobacion), 0010 (quitar `abierto`) en proyectos/migrations/
- [X] T009 [US1] Servicio: `marcar_actual`, `periodo_actual()` con caché; asignar período al enviar (error si no hay) y al aprobar en proyectos/servicios.py y proyectos/models.py
- [X] T010 [US1] Formulario sin período (FormularioProyecto) y FormularioPeriodo sin `abierto` en proyectos/forms.py
- [X] T011 [US1] Vistas y rutas: marcar actual con confirmación (GET/POST), quitar abrir/cerrar, enviar muestra el error, en proyectos/views.py, proyectos/urls.py y proyectos/templates/proyectos/periodos.html, periodo_confirmar_actual.html, formulario.html, enviar.html
- [X] T012 [US1] Procesador `periodo_actual` en config/contexto.py y config/settings.py; pie en templates/parciales/pie.html
- [X] T013 [US1] Verificación y certificado con `periodo_aprobacion` en vitrina/templates/vitrina/verificado.html y vitrina/verificacion.py; admin de Django en proyectos/admin.py
- [X] T014 [US1] Traducciones (locale/en/LC_MESSAGES/django.po → .mo) y entrada en APRENDIZAJE.md

## Phase 4: User Story 2 — Arreglos rápidos (P1)

**Goal**: ayuda del correo por proveedor, textos sin tofu y "Guardados" unificado.
**Independent Test**: cada arreglo por separado.

- [X] T015 [P] [US2] Pruebas del correo (bloques por proveedor, enlaces externos, error 5.7.139/5.7.30) en cuentas/tests/test_correo_envio.py
- [X] T016 [US2] Ayuda por proveedor con JS mínimo y sin JS los tres bloques, en cuentas/templates/cuentas/correo_envio.html y static/js/correo.js; mensaje Microsoft en cuentas/correo_envio.py
- [X] T017 [P] [US2] Pruebas de tildes: NFC al guardar, inicial por grafema, glifos del título de ejemplo en las fuentes del PDF (reportlab TTFontFile), en vitrina/tests/test_tildes.py
- [X] T018 [US2] Normalizar NFC (utilidad en config/texto.py) en proyectos/forms.py, comunidad/forms.py, cuentas/forms.py; migración de datos proyectos/migrations/0011; filtro `inicial` en vitrina/templatetags/iconos.py; PDF en vitrina/verificacion.py
- [X] T019 [P] [US2] Pruebas de Guardados (textos, redirección de la URL vieja) en comunidad/tests/test_comunidad.py
- [X] T020 [US2] "Guardados" en comunidad/views.py, comunidad/urls.py, comunidad/models.py (verbose_name + migración), comunidad/templates/comunidad/, templates/parciales/encabezado.html y paneles
- [X] T021 [US2] Traducciones y entrada en APRENDIZAJE.md

## Phase 5: User Story 3 — Plan de estudios (P2)

**Goal**: planes y asignaturas administrables; selector agrupado por plan y semestre.
**Independent Test**: crear plan y asignaturas, verlas en el formulario, desactivar y no borrar en uso.

- [X] T022 [US3] Pruebas: CRUD con permisos, no borrar en uso, desactivada conservada, selector agrupado, migración a "Plan vigente", en proyectos/tests/test_planes.py
- [X] T023 [US3] Modelos data-model.md `PlanEstudio.*`, `Asignatura.plan`, `Asignatura.codigo`, `Asignatura.nombre` (único por plan) en proyectos/models.py; migraciones 0012 (plan nulo + datos "Plan vigente") y 0013 (plan obligatorio, restricción)
- [X] T024 [US3] Formularios y selector agrupado por plan y semestre con búsqueda (static/js/selector.js) en proyectos/forms.py
- [X] T025 [US3] Vistas, rutas y plantillas de planes y asignaturas en proyectos/views.py, proyectos/urls.py, proyectos/templates/proyectos/planes*.html, asignatura_formulario.html; enlace en vitrina/templates/vitrina/paneles/admin.html
- [X] T026 [US3] Filtros de Explorar, panel y certificado con `asignatura.nombre` (revisar vitrina/forms.py); admin de Django; traducciones; APRENDIZAJE.md

## Phase 6: User Story 4 — Perfil público (P2)

**Goal**: un perfil por persona, público para estudiantes y profesores.
**Independent Test**: llenar bloques, verlo como visitante, buscar a la persona.

- [X] T027 [US4] Pruebas: visibilidad por rol, admin solo 404, bloques vacíos ocultos, correo oculto, validación ORCID/GitHub/LinkedIn, relaciones solo de aprobados (sin N+1), búsqueda por autor y bloque Personas, bienvenida "Más tarde", edición por secciones, en cuentas/tests/test_perfil_publico.py y vitrina/tests/test_personas.py
- [X] T028 [US4] Modelos data-model.md `Perfil.*`, `Aptitud.nombre`, `ExperienciaLaboral.*`, `Estudio.*` en cuentas/models.py; señal en cuentas/signals.py y cuentas/apps.py; migraciones 0006 (modelos) y 0007 (datos: un perfil por usuario, slug, bienvenida_vista para cuentas ya usadas)
- [X] T029 [US4] Servicio cuentas/perfiles.py: slug estable, validadores de enlaces, `tiene_perfil_publico`, `personas_relacionadas`, `buscar_personas`, rol mostrado
- [X] T030 [US4] Formularios de cada sección en cuentas/forms.py (foto con config/imagenes.py, aptitudes con datalist)
- [X] T031 [US4] Vistas de edición, bienvenida y rutas en cuentas/views.py y cuentas/urls.py
- [X] T032 [US4] Perfil público `/personas/<slug>/` en vitrina/views.py, vitrina/urls.py, vitrina/templates/vitrina/persona.html y parciales de edición
- [X] T033 [US4] Bienvenida en el panel (vitrina/paneles.py, plantillas de panel); enlaces a perfiles en detalle, revisión y comentarios; Explorar busca por autor y muestra Personas (vitrina/forms.py, vitrina/views.py, explorar.html)
- [X] T034 [US4] Admin de Django, traducciones, README (media/ y fotos) y APRENDIZAJE.md

## Phase 7: User Story 5 — El estudiante elige al revisor (P3)

**Goal**: el creador elige profesor con sugerencias; el profesor acepta o no; solo el asignado revisa.
**Independent Test**: flujo completo con dos profesores.

- [X] T035 [US5] Pruebas: solo el creador elige, exclusiones, sugerencias y motivos, aceptar, no aceptar con y sin mensaje/recomendación, correos, retirar antes/después de 5 días, reenvío al mismo profesor, solo el revisor decide, reasignación del admin, disponibilidad, historial, migración, en proyectos/tests/test_solicitudes.py (y ajustar test_revision.py, test_servicios.py, vitrina/tests/test_paneles.py)
- [X] T036 [US5] Modelos data-model.md `SolicitudRevision.*`, `EventoEstado.accion`, `Proyecto.subestado` en proyectos/models.py; migraciones 0014 (modelos) y 0015 (datos: en revisión → solicitud aceptada)
- [X] T037 [US5] servicios.py: regla `REVISOR_ASIGNADO`, admin ya no decide, bandeja solo del revisor, `registrar_evento`; permisos en proyectos/permisos.py
- [X] T038 [US5] proyectos/solicitudes.py: solicitar, aceptar, no_aceptar, retirar, reasignar, profesores_elegibles, sugerir_profesores
- [X] T039 [US5] Correos (solicitud, aceptó, no aceptó, retirada, reasignada) en proyectos/correos.py y proyectos/templates/proyectos/correos/
- [X] T040 [US5] Vistas y rutas: enviar con elección, elegir revisor, lista de profesores, panel de resumen, retirar, solicitudes, aceptar, no aceptar, reasignar, tomar; plantillas en proyectos/templates/proyectos/
- [X] T041 [US5] Disponibilidad (cuentas/views.py), avisos en el panel del estudiante, insignia de subestado (templates/componentes/insignia_estado.html), historial con acciones
- [X] T042 [US5] (Opcional) Recordatorio al tercer día en proyectos/management/commands/recordar_solicitudes.py
- [X] T043 [US5] Traducciones y APRENDIZAJE.md (explicar subestados)

## Phase 8: User Story 6 — Menú de la cuenta (P4)

**Goal**: barra mínima y menú del avatar con opciones por rol.
**Independent Test**: menú con cada rol, teclado y sin JS.

- [X] T044 [US6] Pruebas: opciones según rol activo, admin solo sin "Mi perfil", cambio de rol desde el menú, visitante ve engranaje, contadores con consultas fijas, Mi cuenta sin JS, en vitrina/tests/test_menu.py
- [X] T045 [US6] Procesador `menu_cuenta` (contadores) en config/contexto.py
- [X] T046 [US6] Encabezado y menú en templates/parciales/encabezado.html, menu_cuenta.html, ajustes_visitante.html; página cuentas/templates/cuentas/mi_cuenta.html
- [X] T047 [US6] static/js/menu.js (aria-expanded, foco, Esc, clic fuera, hoja en celular) y estilos en static/src/entrada.css → static/css/app.css
- [X] T048 [US6] Íconos en botones de acción y enlaces del resto de plantillas; traducciones; APRENDIZAJE.md

## Phase 9: User Story 7 — Portada, color, demo y video (P5)

**Goal**: portada propia o color de paleta y enlaces de demo y video.
**Independent Test**: subir y quitar portada, elegir color, enlaces vacíos ocultos.

- [X] T049 [US7] Pruebas: validación de imagen, paleta (contraste ≥ 4,5), enlaces vacíos ocultos, esquemas no permitidos, og_imagen, en proyectos/tests/test_portada.py
- [X] T050 [US7] Modelos data-model.md `Proyecto.imagen_portada`, `Proyecto.color_portada`, `Proyecto.video`; paleta en proyectos/paleta.py; migraciones 0016 (campos) y 0017 (datos: primera imagen → portada)
- [X] T051 [US7] Formulario con portada, quitar portada, paleta con vista previa (static/js/portada.js) en proyectos/forms.py y formulario.html
- [X] T052 [US7] Tarjeta, detalle (enlaces junto al repositorio) y og_imagen en vitrina/templates/vitrina/_tarjeta_proyecto.html, detalle.html, vitrina/views.py
- [X] T053 [US7] Traducciones y APRENDIZAJE.md

## Phase 10: Polish

- [X] T054 Suite completa en verde, `makemigrations --check`, mensajes compilados, Tailwind recompilado
- [X] T055 README: pasos para quien baja los cambios (migrate, compilemessages, media/, íconos y fuentes)
- [X] T056 Revisión visual (claro/oscuro, 360 px y escritorio) con Chrome headless sobre una base temporal

## Dependencies

- Setup → Foundational → historias en orden P1 (US1, US2) → P2 (US3 → US4) → P3 (US5, necesita US3 y US4) → P4 (US6, usa contadores de US5) → P5 (US7).
- Dentro de cada historia: pruebas → modelos/migraciones → servicios → vistas/plantillas → traducciones.

## Parallel Opportunities

- T003 y T005; en US2 las tres partes (correo, tildes, guardados) son independientes (T015/T017/T019).

## Implementation Strategy

MVP = US1 + US2 (P1). Se implementa y prueba una historia a la vez, y al cerrar cada una se corren
sus pruebas y las de las apps que toca; la suite completa al final de cada prioridad.
