# Tasks: Revisión e historial

**Input**: [spec.md](spec.md) y [plan.md](plan.md). Cada tarea deja su entrada en `APRENDIZAJE.md`.

## Fase 1: Base

- [x] T001 Modelos `EventoEstado` (inmutable) y `Consecutivo`; migración `0003`
- [x] T002 `proyectos/servicios.py`: `TRANSICIONES`, `puede_cambiar`, `cambiar_estado`, `generar_codigo`
- [x] T003 Admin: campos de estado de solo lectura, historial en línea, `EventoEstado` de solo lectura
- [x] T004 Pruebas del servicio (`test_servicios.py`)

## Fase 2: Historia 1 — Enviar (P1)

- [x] T005 `FormularioEnvio`, vista `enviar`, plantilla `enviar.html`, acción en "Mis proyectos"

## Fase 3: Historias 2 y 3 — Bandeja, tomar y decidir (P1)

- [x] T006 Vista `bandeja` con tres vistas y plantilla `bandeja.html`
- [x] T007 Vistas `tomar` y `revisar`, `FormularioDecision`, plantillas `revisar.html` y `_historial.html`
- [x] T008 Correo `avisar_decision` y sus plantillas
- [x] T009 Enlace "Bandeja" en el encabezado

## Fase 4: Historias 4 y 5 — Reenviar e historial (P2)

- [x] T010 Detalle: observación destacada, botones de autor, historial y enlace a revisión

## Fase 5: Cierre

- [x] T011 Pruebas de vistas (`test_revision.py`, `test_detalle.py`)
- [x] T012 Traducciones, Tailwind, revisión visual, README, `APRENDIZAJE.md` y entrega
