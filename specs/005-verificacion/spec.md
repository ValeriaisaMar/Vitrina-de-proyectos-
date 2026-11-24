# Feature Specification: QR, certificado y verificación

**Feature Branch**: `feature/005-verificacion`

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "Cada proyecto aprobado tiene un QR descargable y un certificado PDF con
su código VP-AAAA-NNNN. El QR abre una página pública donde cualquiera comprueba que el proyecto
fue verificado por la carrera. También se puede verificar escribiendo el código."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verificar un proyecto (Priority: P1)

Una persona externa (un reclutador, un jurado) escanea el QR o escribe el código y ve si el
proyecto es auténtico: título, autores, docente que lo aprobó, fecha y código.

**Why this priority**: es la razón de ser del sello de la vitrina.

**Independent Test**: aprobar un proyecto, abrir `/verificar/VP-AAAA-NNNN/` sin sesión y ver los
datos; abrir un código inventado y ver que no es válido.

**Acceptance Scenarios**:

1. **Given** un código de un proyecto aprobado, **When** se abre su página de verificación,
   **Then** se ve el sello "Verificado" con título, autores, docente que aprobó, fecha y código.
2. **Given** un código inexistente o mal escrito, **When** se busca, **Then** se ve un aviso claro
   de que no corresponde a ningún proyecto verificado (y la página directa responde 404).
3. **Given** el formulario de "Verificar QR", **When** se escribe el código en minúsculas o con
   espacios, **Then** igual se encuentra.
4. **Given** la página de verificación, **Then** MUST NOT mostrar correos, comentarios internos,
   historial ni ningún otro dato que no sea público.

---

### User Story 2 - Descargar el QR y el certificado (Priority: P1)

Cualquier persona que ve un proyecto aprobado puede descargar su QR en PNG y su certificado en
PDF; los autores lo usan en su portafolio y hoja de vida.

**Acceptance Scenarios**:

1. **Given** un proyecto aprobado, **When** se descarga el QR, **Then** es un PNG que al escanearse
   abre la página de verificación de su código.
2. **Given** un proyecto aprobado, **When** se descarga el certificado, **Then** es un PDF con el
   nombre de la universidad, la carrera, el título, los autores, la asignatura, el periodo, el
   docente, la fecha, el código y el mismo QR.
3. **Given** un proyecto no aprobado o un código inexistente, **When** se piden el QR o el PDF,
   **Then** la respuesta es 404.
4. **Given** que la persona navega en inglés, **When** descarga el certificado, **Then** sale en inglés.

---

### User Story 3 - Ver la verificación desde el proyecto (Priority: P2)

El detalle de un proyecto aprobado muestra su código, el QR y los botones de descarga; "Mis
proyectos" ofrece el certificado de los aprobados.

### Edge Cases

- La demo se hace en un portátil: un QR que apunte a `127.0.0.1` no abre en un celular. La
  variable opcional `SITIO_URL` fija la dirección base de los QR (por ejemplo la IP de la red).
- No existe el logo oficial todavía: el certificado se genera igual con el nombre en texto y
  usa el logo si se agrega como PNG en `static/img/`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La página `/verificar/` MUST tener un formulario para escribir el código y explicar
  cómo escanear el QR con la cámara del celular.
- **FR-002**: `/verificar/<código>/` MUST mostrar solo título, autores, docente que aprobó, fecha
  de aprobación y código, más el enlace a la ficha pública.
- **FR-003**: El QR MUST codificar la dirección absoluta de `/verificar/<código>/`.
- **FR-004**: QR (PNG) y certificado (PDF) MUST generarse al momento, sin guardarse en disco, y
  solo para proyectos aprobados.
- **FR-005**: El certificado MUST usar los colores y tipografías de la plataforma.
- **FR-006**: `SITIO_URL` MUST ser opcional y leerse de `.env`; sin ella se usa el dominio de la petición.
- **FR-007**: Todo en español e inglés, de 360 a 1920 px.

## Success Criteria *(mandatory)*

- **SC-001**: Escanear el QR con un celular abre la verificación en menos de 5 segundos.
- **SC-002**: El certificado se genera en menos de 1 segundo.
- **SC-003**: `python manage.py test` pasa completo.

## Assumptions

- El QR y el certificado son públicos para proyectos aprobados: no contienen nada que no esté
  ya en la página pública.
- Los códigos son consecutivos y por eso adivinables; no es un problema porque solo llevan a
  datos públicos.
- Para el PDF se convirtieron una vez las fuentes del sitio (woff2) a TTF en `static/fonts/pdf/`;
  reportlab no lee woff2. Misma licencia OFL.
