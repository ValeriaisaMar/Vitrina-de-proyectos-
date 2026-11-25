# Feature Specification: Ajustes pedidos por el profesor

**Feature Branch**: `feature/008-ajustes-profesor`

**Created**: 2026-11-24

**Status**: Implemented

**Input**: User description: "Cinco cambios que pidió el profesor: un usuario puede tener varios
roles y elige con cuál entrar; el admin administra los periodos académicos; el admin configura
desde la app el correo que envía los mensajes; los comentarios llevan la etiqueta de autor y los
autores pueden responder; identidad visual completa (logos, favicon y vista previa al compartir)."

## Clarifications

### Session 2026-11-24

- Q: ¿Se puede editar el rol de una cuenta técnica (superusuario de Django) desde la app? → A: No,
  como hasta ahora: sus roles y su estado se cambian en `/admin/`.
- Q: ¿Las acciones de autor (editar, enviar, salir, transferir) dependen del rol activo? → A: Sí,
  son del rol estudiante. Ver un proyecto propio no depende del rol.
- Q: ¿Qué periodos quedan abiertos al migrar? → A: Los del año actual o posteriores; los anteriores
  quedan cerrados. Además se crea el del semestre actual si no existía.
- Q: `validar_periodo` está importado por la migración 0001, que no se puede modificar. → A: Se
  conserva solo para esa migración, documentado; el código ya no la usa.
- Q: Dependencia `cryptography` (principio XII). → A: Aprobada por el equipo; constitución 2.1.0.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Varios roles y "Entrar como" (Priority: P1)

Una persona puede tener a la vez los roles estudiante, profesor y admin. Si tiene más de uno, en el
menú de su cuenta elige con cuál actúa; lo que ve y puede hacer depende de ese rol activo.

**Acceptance Scenarios**:

1. **Given** un admin en la gestión de usuarios, **When** marca o desmarca casillas de rol,
   **Then** la persona queda con esos roles y queda registrado quién lo hizo y cuándo.
2. **Given** una persona con dos roles, **When** abre el menú de su cuenta, **Then** ve "Entrar
   como" con sus roles y el actual marcado; al elegir otro (POST con CSRF) llega al panel de ese rol.
3. **Given** una persona con un solo rol, **Then** ve su rol como etiqueta, sin selector.
4. **Given** cualquier página con sesión, **Then** el rol activo se ve en el encabezado.
5. **Given** que inicia sesión, **Then** entra con el último rol que usó (si todavía lo tiene) o con
   el de menor privilegio.
6. **Given** el perfil, **Then** la sección "Mis roles" muestra sus roles y desde cuándo.
7. **Given** el registro público, **Then** la cuenta se crea solo con el rol estudiante.

**Reglas de seguridad**:

- Un rol ajeno puesto a mano en la sesión se ignora y se usa el rol por defecto.
- Si un admin le quita el rol activo, en la siguiente petición pasa a su rol por defecto.
- Toda cuenta conserva al menos un rol; no se le quita el rol admin al último admin activo;
  quitarse el rol admin a uno mismo pide confirmación.
- Conflicto de interés: quien actúa como profesor o admin no revisa, aprueba ni rechaza un
  proyecto del que es autor; ese proyecto no aparece en su bandeja.

---

### User Story 2 - Periodos académicos (Priority: P2)

El admin crea, edita, abre y cierra periodos (ordinarios, intersemestrales, intensivos u otros)
desde la app.

**Acceptance Scenarios**:

1. **Given** el panel del admin, **When** entra a "Periodos", **Then** ve nombre, tipo, fechas,
   abierto/cerrado y número de proyectos, y puede crear, editar, abrir y cerrar.
2. **Given** un estudiante que crea un proyecto, **Then** solo puede elegir periodos abiertos; al
   editar uno cuyo periodo se cerró, lo conserva. Sin periodos abiertos se le avisa.
3. **Given** Explorar, **Then** el filtro ofrece los periodos con proyectos publicados, del más
   reciente al más antiguo, con un slug legible en la URL.
4. **Given** un periodo con proyectos, **Then** no se puede borrar (se ofrece cerrarlo).
5. La verificación y el certificado muestran el nombre del periodo.

---

### User Story 3 - Correo de envío configurable (Priority: P3)

El admin cambia desde la app la cuenta SMTP que envía los correos.

**Acceptance Scenarios**:

1. **Given** un usuario sin rol activo admin, **When** abre "Correo de envío", **Then** recibe 403.
2. **Given** el formulario, **Then** tiene servidor, puerto, seguridad, usuario, contraseña de
   aplicación, nombre y correo del remitente, y botones Gmail, Outlook y Personalizado.
3. **Given** una contraseña guardada, **Then** nunca se vuelve a mostrar y dejar el campo vacío la conserva.
4. **Given** "Probar configuración", **Then** se envía un correo de prueba al admin con los datos del
   formulario sin guardarlos, con errores comprensibles y límite de intentos.
5. **Given** que no hay configuración guardada, **Then** el correo funciona como antes (`.env` o consola).

---

### User Story 4 - Comentarios: etiqueta de autor y respuestas (Priority: P4)

**Acceptance Scenarios**:

1. **Given** un comentario de un autor del proyecto, **Then** lleva la etiqueta "Autor" y se destaca
   (borde izquierdo verde grueso, fondo verde suave, etiqueta amarilla con texto oscuro).
2. **Given** un autor del proyecto, **Then** puede responder comentarios; nadie más puede.
3. Un solo nivel de respuesta, con sangría y en orden cronológico.
4. **Given** un comentario oculto, **Then** sus respuestas dejan de mostrarse al público.
5. *Opcional (hecho):* etiqueta "Docente revisor" y correo a quien comentó cuando un autor responde.

---

### User Story 5 - Identidad visual completa (Priority: P5)

Favicon, íconos, manifest y Open Graph en todas las páginas; logo claro/oscuro en el encabezado;
sellos en el pie, en las páginas de cuentas y en la verificación; logo y sellos en el certificado
PDF; logo en los correos HTML y en las páginas de error; vista previa del proyecto al compartir.

## Requirements *(mandatory)*

- **FR-001**: Los roles viven en `RolAsignado(usuario, rol, asignado_por, asignado_en)` con
  restricción única `(usuario, rol)`; cada cambio queda en `CambioRol`.
- **FR-002**: `RolActivoMiddleware` valida el rol de la sesión y lo deja en `request.user.rol_activo`.
- **FR-003**: `rol_requerido` y todos los permisos comprueban el rol activo; los conteos y avisos
  "a todos los que tienen el rol" usan `tiene_rol`.
- **FR-004**: `Proyecto.periodo` es `ForeignKey(Periodo, on_delete=PROTECT)`; la migración conserva
  los datos y es reversible.
- **FR-005**: La contraseña del correo se guarda cifrada con Fernet (`CLAVE_CIFRADO`), nunca se
  registra en logs ni aparece en el admin de Django.
- **FR-006**: `Comentario.respuesta_a` con validación de un solo nivel en el modelo y en la vista.
- **FR-007**: Toda cadena nueva traducida al inglés; migraciones sin pendientes.

## Success Criteria *(mandatory)*

- **SC-001**: La suite completa queda en verde, incluidas las pruebas nuevas de cada historia.
- **SC-002**: `makemigrations --check` no detecta cambios.
- **SC-003**: Ningún proyecto, autoría, evento del historial ni comentario se pierde al migrar.
