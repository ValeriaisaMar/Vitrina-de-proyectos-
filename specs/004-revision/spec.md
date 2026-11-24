# Feature Specification: Revisión e historial

**Feature Branch**: `feature/004-revision`

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "Los estudiantes envían sus proyectos a revisión. Cualquier profesor
toma un proyecto de una bandeja común y decide: aprobar, pedir cambios o rechazar, con comentario
obligatorio para pedir cambios o rechazar. Cada cambio de estado queda en un historial que nadie
puede editar. Al aprobarse, el proyecto recibe su código VP-AAAA-NNNN."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enviar un proyecto a revisión (Priority: P1)

Un autor envía su proyecto en Borrador para que un docente lo revise. Puede dejar un mensaje
opcional para el docente. Desde ese momento ya no puede editarlo ni eliminarlo.

**Why this priority**: sin envío no hay nada que revisar.

**Independent Test**: crear un borrador, enviarlo y comprobar que queda en Enviado, que aparece
en la bandeja y que el autor ya no puede editarlo.

**Acceptance Scenarios**:

1. **Given** un autor y un proyecto en Borrador, **When** lo envía, **Then** queda en Enviado,
   se registra el evento en el historial y aparece en la bandeja de los profesores.
2. **Given** un estudiante que no es autor, un profesor o un visitante, **When** intenta enviarlo,
   **Then** recibe 403 (o va al inicio de sesión).
3. **Given** un proyecto ya enviado, en revisión, aprobado o rechazado, **When** un autor
   intenta enviarlo, **Then** no se puede.

---

### User Story 2 - Tomar un proyecto de la bandeja (Priority: P1)

Un profesor ve la bandeja común con los proyectos enviados (los más antiguos primero) y toma uno.
El proyecto pasa a En revisión y queda a su nombre; desaparece de "Por revisar" para los demás.

**Why this priority**: es la puerta de entrada de la revisión docente.

**Independent Test**: con dos profesores, uno toma un proyecto y el otro ya no puede tomarlo.

**Acceptance Scenarios**:

1. **Given** un profesor o admin y un proyecto Enviado, **When** lo toma, **Then** queda En
   revisión con ese revisor y se registra el evento.
2. **Given** que otro profesor ya lo tomó, **When** un segundo profesor intenta tomarlo, **Then**
   ve un aviso y el proyecto sigue con el primero.
3. **Given** un estudiante o un visitante, **When** abre la bandeja, **Then** recibe 403 (o va al
   inicio de sesión).

---

### User Story 3 - Decidir sobre un proyecto (Priority: P1)

El profesor que tomó el proyecto (o un admin) lo revisa con toda su información y decide:
aprobar, pedir cambios o rechazar. Pedir cambios y rechazar exigen un comentario. Los autores
reciben un correo con la decisión.

**Why this priority**: es lo que convierte un proyecto en "verificado".

**Independent Test**: aprobar un proyecto y comprobar que aparece en Explorar con su código;
pedir cambios en otro y comprobar que el autor ve la observación y puede editarlo.

**Acceptance Scenarios**:

1. **Given** el profesor que tomó el proyecto, **When** lo aprueba, **Then** queda Aprobado, con
   fecha de aprobación, revisor y un código `VP-AAAA-NNNN` único, y aparece en Explorar.
2. **Given** el profesor que lo tomó, **When** pide cambios o rechaza sin comentario, **Then** el
   formulario lo impide; con comentario, el estado cambia y el comentario queda en el historial.
3. **Given** otro profesor que no lo tomó, **When** intenta decidir, **Then** recibe 403. Un admin
   sí puede decidir sobre cualquier proyecto en revisión.
4. **Given** una decisión, **When** se guarda, **Then** cada autor recibe un correo con el
   resultado, el comentario y el enlace al proyecto. Si el correo falla, la decisión se guarda igual.

---

### User Story 4 - Corregir y reenviar (Priority: P2)

Un proyecto Con observaciones vuelve a ser editable. Los autores ven la observación destacada en
el detalle, corrigen y lo reenvían; vuelve a la bandeja marcado como reenviado.

**Why this priority**: cierra el ciclo de mejora que pide el curso.

**Independent Test**: pedir cambios, editar como autor, reenviar y verlo de nuevo en la bandeja.

**Acceptance Scenarios**:

1. **Given** un proyecto Con observaciones, **When** un autor abre su detalle, **Then** ve la
   última observación con el nombre del docente y los botones Editar y Reenviar.
2. **Given** que lo reenvía, **Then** queda Enviado y la bandeja indica quién lo revisó antes.

---

### User Story 5 - Ver el historial (Priority: P2)

Autores, profesores y admins ven en el detalle la línea de tiempo del proyecto: cada cambio con
fecha, quién lo hizo y su comentario. El público no ve el historial.

**Acceptance Scenarios**:

1. **Given** un autor, profesor o admin, **When** abre el detalle, **Then** ve el historial completo.
2. **Given** un visitante y un proyecto aprobado, **When** abre el detalle, **Then** no ve el historial.
3. **Given** cualquier usuario, incluido un admin en el panel de Django, **When** intenta editar o
   borrar un evento del historial, **Then** no puede.

### Edge Cases

- Dos profesores pulsan "Tomar" al mismo tiempo: solo uno lo consigue (bloqueo de fila).
- Dos proyectos se aprueban al mismo tiempo: reciben códigos distintos y consecutivos.
- Un profesor que tomó un proyecto deja de estar disponible: un admin puede decidir por él.
- El correo de decisión falla: la decisión se guarda y el error queda en el registro.
- Un proyecto que salió de Borrador no se puede eliminar, ni desde la web ni desde el panel.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todo cambio de estado MUST pasar por `proyectos/servicios.py::cambiar_estado`, que
  valida la transición, el permiso y el comentario y registra el evento.
- **FR-002**: Las únicas transiciones MUST ser las de la constitución (principio VII).
- **FR-003**: Pedir cambios y rechazar MUST exigir un comentario; enviar y aprobar lo admiten opcional.
- **FR-004**: Cada evento MUST guardar estado anterior, estado nuevo, actor, comentario y fecha, y
  MUST NOT poder editarse ni borrarse (tampoco desde el panel de Django).
- **FR-005**: Al aprobar, el sistema MUST asignar un código `VP-AAAA-NNNN` (año de aprobación y
  consecutivo de ese año) que no cambia nunca.
- **FR-006**: El panel de Django MUST NOT permitir cambiar a mano estado, revisor, código ni fecha
  de aprobación.
- **FR-007**: La bandeja MUST tener tres vistas: "Por revisar" (Enviado), "En revisión" (las del
  profesor; el admin ve todas) y "Decididos por mí".
- **FR-008**: Los autores MUST recibir un correo con cada decisión.
- **FR-009**: Profesores y admins MUST tener un enlace "Bandeja" en el encabezado.
- **FR-010**: Todas las páginas nuevas MUST estar en español e inglés y funcionar de 360 a 1920 px.

### Key Entities

- **EventoEstado**: proyecto, estado anterior, estado nuevo, actor, comentario y fecha.
- **Consecutivo**: año y último número usado, para generar los códigos sin repetirlos.

## Success Criteria *(mandatory)*

- **SC-001**: Un profesor toma y decide un proyecto en menos de 2 minutos.
- **SC-002**: El 100 % de los cambios de estado quedan en el historial.
- **SC-003**: No existe forma, desde la web ni desde el panel, de aprobar sin pasar por la revisión.
- **SC-004**: `python manage.py test` pasa completo, con pruebas de cada transición y permiso.

## Assumptions

- Los profesores se crean como cualquier cuenta y un admin les cambia el rol a Profesor desde
  `/admin/` (el panel de usuarios propio llega en el módulo 006).
- Un profesor no puede "soltar" un proyecto que tomó; si hace falta, un admin decide por él.
- El código se genera en este módulo porque nace con la aprobación; el QR, el certificado PDF y la
  página pública de verificación llegan en el 005.
- Los correos de decisión van en español, el idioma por defecto de la plataforma.
