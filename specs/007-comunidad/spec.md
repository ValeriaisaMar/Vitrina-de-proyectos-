# Feature Specification: Comunidad

**Feature Branch**: `feature/007-comunidad`

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "Las personas con cuenta pueden dar me gusta, guardar proyectos en
favoritos y comentar. Los comentarios se publican al momento y los pueden ocultar los autores del
proyecto y los admins."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Me gusta (Priority: P1)

Cualquier persona con cuenta da (o quita) me gusta a un proyecto aprobado. El total se ve en la
ficha y en las tarjetas, y Explorar puede ordenar por los más gustados.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión y un proyecto aprobado, **When** pulsa "Me gusta", **Then** el
   total sube en uno; si vuelve a pulsar, lo quita.
2. **Given** un autor del proyecto, **Then** no puede darse me gusta a sí mismo.
3. **Given** un visitante, **When** pulsa el botón, **Then** va a iniciar sesión y vuelve al proyecto.
4. **Given** Explorar, **When** se ordena por "Más gustados", **Then** los proyectos salen de mayor a menor.

---

### User Story 2 - Favoritos (Priority: P2)

Cualquier persona con cuenta guarda proyectos para verlos después en "Mis favoritos" (privado).

**Acceptance Scenarios**:

1. **Given** un usuario con sesión, **When** guarda un proyecto, **Then** aparece en "Mis
   favoritos"; si lo quita, desaparece.
2. **Given** otro usuario, **Then** nunca ve los favoritos ajenos.

---

### User Story 3 - Comentar (Priority: P1)

Cualquier persona con cuenta comenta un proyecto aprobado. El comentario se publica al momento.
Quien lo escribió puede borrarlo.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión, **When** escribe un comentario de 2 a 1000 caracteres,
   **Then** se publica con su nombre y la fecha.
2. **Given** un comentario vacío o demasiado largo, **Then** se rechaza con un mensaje claro.
3. **Given** que alguien publica más de 5 comentarios en 10 minutos, **Then** se le pide esperar.
4. **Given** el autor del comentario, **When** lo borra, **Then** desaparece; nadie más puede borrarlo.
5. **Given** un comentario con HTML o un script, **Then** se muestra como texto, nunca se ejecuta.

---

### User Story 4 - Moderar comentarios (Priority: P1)

Los autores del proyecto y los admins ocultan comentarios inapropiados (y los pueden volver a mostrar).

**Acceptance Scenarios**:

1. **Given** un autor o coautor del proyecto, o un admin, **When** oculta un comentario,
   **Then** el público deja de verlo; los moderadores lo ven marcado como "Oculto" y pueden mostrarlo.
2. **Given** cualquier otra persona, **When** intenta ocultar un comentario, **Then** recibe 403.

### Edge Cases

- Solo los proyectos aprobados tienen comunidad; en un borrador o un proyecto en revisión las
  acciones responden 404.
- Una cuenta desactivada no puede comentar (ni iniciar sesión); sus comentarios se conservan.

## Requirements *(mandatory)*

- **FR-001**: Me gusta y favorito MUST ser únicos por usuario y proyecto (restricción en la base).
- **FR-002**: Todas las acciones MUST ser POST con CSRF y funcionar sin JavaScript.
- **FR-003**: Ocultar MUST quedar registrado (quién y cuándo) y ser reversible; no borra el texto.
- **FR-004**: El texto de los comentarios MUST escaparse siempre (constitución, III).
- **FR-005**: Español e inglés, de 360 a 1920 px, claro y oscuro.

## Success Criteria *(mandatory)*

- **SC-001**: Dar me gusta o comentar toma un clic o un envío, sin salir de la ficha.
- **SC-002**: Explorar sigue mostrando 12 tarjetas con un número fijo de consultas.
- **SC-003**: `python manage.py test` pasa completo.

## Assumptions

- Los comentarios no avisan por correo a los autores (evita correos de más); los ven en la ficha.
- No hay respuestas en hilo ni edición de comentarios: se borran y se escriben de nuevo.
