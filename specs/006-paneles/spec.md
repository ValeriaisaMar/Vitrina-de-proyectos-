# Feature Specification: Paneles por rol

**Feature Branch**: `feature/006-paneles`

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "Cada usuario (estudiante, profesor, admin) ve la aplicación de una manera:
un panel propio al entrar. El admin gestiona usuarios y roles sin tener que usar el panel de Django."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Panel del estudiante (Priority: P1)

Al entrar, el estudiante ve cuántos proyectos tiene en cada etapa, lo que requiere su atención
(observaciones por corregir, borradores sin enviar) y sus certificados listos para descargar.

**Acceptance Scenarios**:

1. **Given** un estudiante con proyectos en varios estados, **When** abre su panel, **Then** ve las
   cifras por etapa, los proyectos con observaciones (con la última observación) y los borradores.
2. **Given** proyectos aprobados, **Then** el panel ofrece su certificado y su página de verificación.
3. **Given** un estudiante sin proyectos, **Then** el panel lo invita a crear el primero.

---

### User Story 2 - Panel del profesor (Priority: P1)

El profesor ve cuántos proyectos esperan revisión, los que lleva él, los que esperan hace más
tiempo (para tomarlos desde ahí) y sus últimas decisiones.

**Acceptance Scenarios**:

1. **Given** proyectos enviados, **When** el profesor abre su panel, **Then** ve el total y los
   tres que más tiempo llevan esperando, con el botón Tomar.
2. **Given** decisiones tomadas por él, **Then** ve cuántos aprobó, en cuántos pidió cambios y
   cuántos rechazó, y sus últimas cinco decisiones.

---

### User Story 3 - Panel del admin (Priority: P1)

El admin ve el estado de toda la plataforma: usuarios por rol, proyectos por estado, proyectos que
esperan más de 3 días, aprobados por periodo, tecnologías más usadas y la actividad reciente.

**Acceptance Scenarios**:

1. **Given** datos en la plataforma, **When** el admin abre su panel, **Then** ve esas cifras con
   barras legibles (cada barra con su número escrito).
2. **Given** un estudiante o profesor, **When** intenta ver datos del panel del admin, **Then** no
   puede: cada rol solo ve su propio panel.

---

### User Story 4 - Gestionar usuarios y roles (Priority: P1)

El admin busca usuarios por nombre o correo, filtra por rol y estado, cambia el rol (estudiante,
profesor, admin) y desactiva o reactiva cuentas.

**Acceptance Scenarios**:

1. **Given** el admin, **When** cambia el rol de un usuario, **Then** el cambio se guarda y queda
   registrado (quién, cuándo, de qué rol a qué rol) en el registro de acciones de Django.
2. **Given** el admin, **When** desactiva una cuenta, **Then** esa persona ya no puede iniciar
   sesión, pero sus proyectos y su historial se conservan.
3. **Given** el admin, **When** intenta cambiar su propio rol o desactivarse, **Then** no puede
   (así nunca se queda la plataforma sin admin por error).
4. **Given** un profesor con proyectos en revisión, **When** el admin le quita el rol, **Then** se
   avisa que esos proyectos los tendrá que decidir un admin.
5. **Given** una cuenta técnica (superusuario de Django), **Then** su rol y estado no se cambian
   desde aquí, solo desde `/admin/`.
6. **Given** un estudiante o profesor, **When** abre la gestión de usuarios, **Then** recibe 403.

### Edge Cases

- Una cuenta que nunca se activó se muestra como "Sin activar", distinta de una desactivada.
- Al pasar a un estudiante a profesor, sus proyectos siguen siendo suyos.
- Promover a admin no da acceso a `/admin/` de Django (eso sigue siendo `is_staff`, técnico).

## Requirements *(mandatory)*

- **FR-001**: `/panel/` MUST mostrar el panel del rol de quien entra; sin sesión, ir al inicio de sesión.
- **FR-002**: Después de iniciar sesión o activar la cuenta, la persona MUST llegar a su panel
  (salvo que viniera de otra página con `?next=`).
- **FR-003**: Solo el admin MUST poder cambiar roles y activar o desactivar cuentas (constitución, V).
- **FR-004**: Los cambios de rol y de estado MUST registrarse con `LogEntry` de Django.
- **FR-005**: La lista de usuarios MUST tener búsqueda, filtros y paginación de 20.
- **FR-006**: El menú de cuenta MUST tener "Mi panel"; las cifras MUST mostrar su número, no solo
  una barra.
- **FR-007**: Español e inglés, de 360 a 1920 px, claro y oscuro.

## Success Criteria *(mandatory)*

- **SC-001**: Un admin nombra a un profesor en menos de 30 segundos.
- **SC-002**: Cada panel carga con un número fijo de consultas, sin importar cuántos proyectos haya.
- **SC-003**: `python manage.py test` pasa completo.

## Assumptions

- "Mis proyectos" sigue existiendo como la tabla completa; el panel del estudiante es el resumen.
- La bandeja sigue siendo el lugar de trabajo del profesor; su panel es el resumen.
- Los catálogos (asignaturas y tecnologías) se siguen administrando en `/admin/`; el panel enlaza ahí.
