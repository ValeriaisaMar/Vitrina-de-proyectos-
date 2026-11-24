# Tasks: Proyectos, explorar y detalle

**Input**: [spec.md](spec.md) y [plan.md](plan.md). Cada tarea deja su entrada en `APRENDIZAJE.md`.

## Fase 1: Modelos y datos

- [x] T001 Modelos `Asignatura`, `Tecnologia`, `Estado`, `Proyecto`, `Autoria` e `Imagen`
- [x] T002 `proyectos/validadores.py` (PDF, imágenes, periodo)
- [x] T003 Migración `0001_initial` y migración de datos `0002_datos_iniciales` (malla UTEQ + tecnologías)
- [x] T004 Admin de asignaturas, tecnologías y proyectos (con autorías e imágenes)

## Fase 2: Historias 1 y 2 — Crear, editar y eliminar (P1)

- [x] T005 [US1] `FormularioProyecto` con coautores, tecnologías, imágenes y PDF
- [x] T006 [US1] `proyectos/permisos.py` y vistas `crear`, `editar`, `eliminar`, `mis_proyectos`
- [x] T007 [US1] Plantillas `formulario.html`, `mis_proyectos.html`, `confirmar_eliminar.html`
- [x] T008 [US1/US2] Pruebas en `proyectos/tests/`

## Fase 3: Historias 3 y 4 — Explorar y detalle (P1)

- [x] T009 [US3] `FormularioFiltros` y vista `explorar` con búsqueda, filtros, orden y paginación
- [x] T010 [US4] Vista `detalle` con vista previa para autores, profesores y admins
- [x] T011 [US3/US4] Plantillas `explorar.html`, `detalle.html`, `_tarjeta_proyecto.html`
- [x] T012 [US3/US4] Pruebas en `vitrina/tests/test_explorar.py` y `test_detalle.py`

## Fase 4: Historia 5 — Portada (P2)

- [x] T013 [US5] Cifras y destacados en `inicio`; pruebas en `vitrina/tests/test_portada.py`

## Fase 5: Cierre

- [x] T014 Encabezado con "Mis proyectos"; traducciones; Tailwind
- [x] T015 Revisión visual, `python manage.py test` en verde, `APRENDIZAJE.md` y entrega
