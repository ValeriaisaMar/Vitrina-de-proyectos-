# Feature Specification: Perfiles, profesor revisor elegido, período actual y navegación

**Feature Branch**: `feat/009-perfiles-y-revisor`

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "Siete cambios: un solo período actual que designa el admin; arreglos
rápidos (instrucciones del correo según proveedor, tildes en la portada de color, «Favoritos» pasa a
«Guardados»); plan de estudios y asignaturas administrables; perfil público de cada usuario; el
estudiante elige al profesor que revisa su proyecto; menú de la cuenta con íconos y opciones
rápidas; portada, color, demo y video del proyecto." (documento `prompt-009-perfiles-y-revisor.md`).

## Clarifications

### Session 2026-11-25

Decisiones tomadas al especificar (sin preguntas abiertas; se pueden corregir antes del plan):

- Q: ¿Nuevos estados para "Por asignar revisor" y "Esperando aceptación"? → A: No. Son
  **subestados de Enviado** que se deducen de las solicitudes: Enviado sin revisor ni solicitud
  pendiente = "Por asignar revisor"; con solicitud pendiente = "Esperando aceptación"; con revisor ya
  asignado (reenvío o reasignación del admin) = "Por revisar". La tabla de transiciones no gana estados.
- Q: ¿Quién envía? → A: Cualquier autor puede enviar (como hoy), pero solo el **creador** elige al
  profesor. Si envía un coautor, el proyecto queda "Por asignar revisor" y el creador ve el aviso.
- Q: ¿El admin sigue pudiendo aprobar? → A: No. Solo el profesor asignado revisa y decide. El admin
  reasigna el revisor (puede asignarse a sí mismo si además tiene el rol profesor).
- Q: Al aceptar una solicitud, ¿pasa directo a En revisión? → A: Sí. En un reenvío con observaciones
  o tras una reasignación, el proyecto queda Enviado con el mismo revisor y este pulsa "Revisar".
- Q: Las acciones del flujo de solicitudes (solicitado, no aceptó, retirada, reasignado) no cambian
  el estado. → A: Se registran en el mismo historial, con un campo "acción"; el historial sigue
  siendo inmutable.
- Q: Tamaño máximo de foto de perfil y portada: el documento dice 5 MB y la constitución 3 MB. →
  A: 5 MB para estas dos imágenes, con enmienda de la constitución (principio III). La galería sigue en 3 MB.
- Q: `fontTools` no es una dependencia aprobada. → A: Se usa solo como herramienta de revisión
  fuera del proyecto; las pruebas comprueban los glifos con el lector TTF de reportlab (aprobado).
- Q: Cambios a la constitución (estados, permisos de revisión, tamaño de imagen). → A: Se enmienda
  a la versión 3.0.0 en esta misma rama; el equipo la aprueba al revisar el Pull Request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Un solo período actual (Priority: P1)

Solo puede haber un período habilitado para recibir proyectos: el actual, que designa el admin.

**Why this priority**: todo envío depende del período; además reemplaza "varios periodos abiertos".

**Independent Test**: marcar un período como actual, enviar un proyecto y ver que lo toma; aprobarlo
y ver el período de aprobación en la verificación.

**Acceptance Scenarios**:

1. **Given** la sección "Periodos", **When** el admin pulsa "Marcar como período actual" en otro
   período y confirma, **Then** ese queda como actual y el anterior deja de serlo; la lista muestra
   claramente cuál es el actual.
2. **Given** un estudiante creando o editando un proyecto, **Then** el formulario ya no pide período;
   los borradores no tienen período.
3. **Given** un proyecto que se envía, **Then** toma el período actual en ese momento.
4. **Given** que no hay período actual, **When** el estudiante intenta enviar, **Then** no puede y
   ve "No hay un período académico activo. Avísale a la administración."
5. **Given** un proyecto aprobado, **Then** guarda el período en que se aprobó, y la verificación y
   el certificado muestran ese período.
6. **Given** cualquier página, **Then** el pie dice "Período académico actual: <nombre>" (si hay).
7. Explorar sigue filtrando por todos los períodos que tienen proyectos publicados.

---

### User Story 2 - Arreglos rápidos: correo, tildes y "Guardados" (Priority: P1)

**Why this priority**: son errores visibles y confusiones que ya reportaron.

**Independent Test**: cada arreglo se comprueba solo (página de correo, una portada con tildes, el
botón Guardar).

**Acceptance Scenarios**:

1. **Given** "Correo de envío", **When** el admin pulsa Gmail, Outlook o Personalizado, **Then** ve
   solo las instrucciones de ese proveedor (sin JavaScript se ven las tres, cada una con su título).
2. Las instrucciones de Gmail y Outlook enlazan (pestaña nueva) a la página de contraseñas de
   aplicación de Google y a la de información de seguridad de Microsoft; Outlook muestra el aviso
   sobre cuentas personales arriba de los pasos.
3. **Given** "Probar configuración", **When** el servidor responde 5.7.139 o 5.7.30, **Then** se
   explica que Microsoft bloqueó el inicio de sesión con contraseña.
4. **Given** un proyecto sin imagen titulado "Diseño de ñandúes: Árbol, pingüino y «más» ¿sí?",
   **Then** su portada de color, su detalle y su certificado muestran todos los caracteres bien.
5. **Given** un proyecto publicado, **Then** el botón dice "Guardar"/"Guardado" con ícono de
   marcador y la sección se llama "Guardados" en todas partes; la dirección vieja redirige a la nueva.

---

### User Story 3 - Plan de estudios y asignaturas administrables (Priority: P2)

El admin mantiene los planes de estudio y sus asignaturas desde la app.

**Why this priority**: las sugerencias de profesores (historia 5) y los perfiles dependen de listas limpias.

**Independent Test**: crear un plan con asignaturas, verlas en el formulario de proyecto agrupadas
por plan y semestre, y desactivar una.

**Acceptance Scenarios**:

1. **Given** "Plan de estudios" en el panel del admin, **Then** puede crear, editar, activar y
   desactivar planes (nombre, año) y sus asignaturas (nombre, código opcional, semestre 1–10, activa).
2. Puede haber varios planes activos; los formularios muestran solo planes y asignaturas activos,
   agrupados por plan y semestre, con búsqueda.
3. **Given** un proyecto o profesor con una asignatura desactivada, **Then** la conserva y se sigue mostrando.
4. **Given** una asignatura o un plan en uso, **Then** no se puede borrar (se ofrece desactivarlo).
5. Las asignaturas existentes quedan dentro de un plan "Plan vigente" sin perder ningún proyecto.

---

### User Story 4 - Perfil público de cada usuario (Priority: P2)

Cada estudiante y profesor tiene un perfil público con lo que quiera contar de sí.

**Why this priority**: conecta proyectos con personas y alimenta la elección de revisor.

**Independent Test**: llenar algunos bloques del perfil, verlo como visitante y buscar a la persona en Explorar.

**Acceptance Scenarios**:

1. **Given** un usuario con rol estudiante o profesor, **Then** su perfil se ve en `/personas/<slug>/`
   también sin sesión; si solo es admin, la dirección da 404 y su menú no tiene "Mi perfil".
2. El perfil dice "Profesor" si tiene ese rol (aunque también sea estudiante); si no, "Estudiante".
3. Cada bloque (foto o iniciales, descripción, aptitudes, experiencia, estudios, GitHub, LinkedIn,
   ORCID, asignaturas que imparte y disponibilidad —profesores—, proyectos publicados, personas
   relacionadas) aparece solo si tiene contenido. El correo nunca se muestra.
4. **Given** el dueño, **Then** ve "Editar perfil" y edita cada sección en la misma página, agregando
   y quitando experiencias y estudios.
5. GitHub acepta la URL o solo el usuario; LinkedIn exige `linkedin.com/in/<id>`; ORCID exige el
   formato `0000-0000-0000-000X` con dígito verificador válido.
6. Personas relacionadas: solo de proyectos aprobados (coautores; profesores que revisaron, o
   estudiantes revisados), sin duplicados y con número de proyectos en común.
7. **Given** el primer inicio de sesión tras activar la cuenta, **Then** aparece "Completa tu perfil"
   con "Completar ahora" y "Más tarde"; "Más tarde" no la vuelve a mostrar y deja un enlace discreto en el panel.
8. Los nombres de autores, del revisor y de quien comenta enlazan a su perfil (si lo tiene).
9. **Given** una búsqueda en Explorar, **Then** encuentra proyectos por título y por autor, y arriba
   muestra el bloque "Personas" con los perfiles cuyo nombre coincide.

---

### User Story 5 - El estudiante elige al profesor que revisa (Priority: P3)

El creador del proyecto elige al profesor revisor con ayuda de sugerencias, y el profesor acepta o no.

**Why this priority**: cambia el flujo de revisión; necesita las historias 3 y 4.

**Independent Test**: enviar un proyecto eligiendo un profesor, aceptarlo como ese profesor y
revisarlo; repetir no aceptando con recomendación.

**Acceptance Scenarios**:

1. **Given** el creador enviando, **Then** ve hasta 5 sugerencias con su motivo ("Imparte Bases de
   datos", "Ha revisado 4 proyectos de esta asignatura") y "Ver todos los profesores" con búsqueda,
   filtros (asignatura, semestre, solo disponibles) y orden (relevancia, nombre, menos pendientes).
2. Cada tarjeta muestra foto, nombre, asignaturas, proyectos revisados y solicitudes pendientes
   (informativo). Al pulsar el nombre se abre un resumen del perfil sin perder la elección.
3. Nunca aparecen los autores. Los no disponibles salen en la lista completa con su etiqueta y no se
   pueden elegir. Quien ya no aceptó este proyecto no sale en las sugerencias, pero sí en la lista
   completa con "Ya rechazó este proyecto" y se puede elegir.
4. **Given** una solicitud, **Then** el profesor recibe un correo y la ve en "Solicitudes de
   revisión" (con contador). **When** acepta, **Then** el proyecto pasa a En revisión a su nombre y
   se avisa a los autores. **When** no acepta (mensaje y recomendación opcionales), **Then** se avisa
   a todos los autores, el proyecto queda "Por asignar revisor" y la recomendación aparece destacada.
5. **Given** una solicitud sin respuesta por 5 días, **Then** el creador puede retirarla y elegir a
   otro; al profesor le llega un aviso. Antes de 5 días no puede.
6. **Given** un proyecto con observaciones que se reenvía, **Then** vuelve al mismo profesor sin elegir.
7. **Given** el admin, **Then** puede reasignar el revisor de cualquier proyecto en revisión o enviado.
8. Solo el profesor asignado revisa, aprueba, pide cambios o rechaza; su bandeja muestra solo sus proyectos.
9. El profesor marca o desmarca "Estoy recibiendo proyectos" en su menú y en su perfil; no afecta a
   lo que ya tiene asignado.
10. Todo (solicitado a, aceptó, no aceptó, retirada, reasignado) queda en el historial.
11. Los proyectos que ya estaban enviados sin revisor quedan "Por asignar revisor" y su creador ve un
    aviso en el panel (sin correo masivo); los que estaban en revisión conservan su revisor.

---

### User Story 6 - Menú de la cuenta con íconos y opciones rápidas (Priority: P4)

La barra superior queda mínima y lo demás vive en el menú del avatar.

**Why this priority**: ordena la navegación que crecieron las historias anteriores.

**Independent Test**: abrir el menú con cada rol activo y con teclado; como visitante, abrir el engranaje.

**Acceptance Scenarios**:

1. Con sesión, la barra tiene logo, "Explorar", buscador y el avatar; como visitante, además
   "Entrar", "Registrarse" y un engranaje con tema e idioma.
2. El menú muestra nombre, rol activo y período actual; cambia de rol con un clic; ofrece Mi perfil
   (si no es solo admin), Panel, las opciones rápidas del rol activo, tema, idioma y Cerrar sesión.
3. Teclado: abre con Enter/Espacio, enfoca el primer ítem, `Esc` cierra y devuelve el foco, clic
   fuera cierra. Sin JavaScript, el avatar lleva a "Mi cuenta" con las mismas opciones.
4. En celular el menú se abre a todo el ancho.
5. Todo ítem de menú, botón de acción y enlace externo lleva ícono.

---

### User Story 7 - Portada, color, demo y video del proyecto (Priority: P5)

**Why this priority**: mejora la presentación, no cambia el flujo.

**Independent Test**: subir una portada, quitarla, elegir un color y agregar los dos enlaces.

**Acceptance Scenarios**:

1. **Given** el formulario, **When** el estudiante sube una portada, **Then** se guarda recortada a
   16:9 y es la cara del proyecto en la vitrina, el detalle y la vista previa al compartir; puede
   quitarla y vuelve la portada de color.
2. Sin portada, elige un color de una paleta de 8 a 10 con buen contraste y lo ve en vivo.
3. "Ver proyecto desplegado" y "Ver video" aparecen junto al repositorio si están llenos, se abren en
   pestaña nueva y solo aceptan `http`/`https`.

### Edge Cases

- Dos admins marcan períodos distintos como actuales a la vez: la base de datos impide dos actuales.
- Un proyecto se envía en un período y se aprueba en otro: conserva ambos.
- Se borra un período que es el actual o que tiene proyectos: no se permite.
- El profesor elegido deja de estar disponible después de recibir la solicitud: la solicitud sigue.
- El profesor elegido pierde el rol profesor: su solicitud pendiente se puede retirar al instante.
- Una cuenta desactivada no aparece como profesor elegible ni en búsquedas de personas.
- Una imagen con extensión .jpg que no es imagen: se rechaza.
- Un usuario cambia su nombre: la dirección de su perfil no cambia.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `Periodo.es_actual` con restricción única condicional; la migración convierte el
  período abierto más reciente en actual y elimina `abierto`.
- **FR-002**: `Proyecto.periodo` es nulo en borrador y se asigna en el servicio de cambio de estado
  al pasar a Enviado; `Proyecto.periodo_aprobacion` se asigna al aprobar (los aprobados existentes
  reciben su período).
- **FR-003**: Un procesador de contexto expone `periodo_actual` con caché invalidada al cambiarlo.
- **FR-004**: Las instrucciones del correo se renderizan en el servidor; los errores 5.7.139/5.7.30
  tienen mensaje propio.
- **FR-005**: Los textos de usuario se normalizan a NFC al guardarse; los existentes se normalizan
  con una migración de datos.
- **FR-006**: "Favoritos" se llama "Guardados" en interfaz, mensajes y traducciones; la URL vieja redirige.
- **FR-007**: `PlanEstudio` y `Asignatura.plan` con restricción única `(plan, nombre)`; `PROTECT` en uso.
- **FR-008**: `Perfil` (uno por usuario, slug estable), `Aptitud`, `ExperienciaLaboral`, `Estudio`,
  `asignaturas_imparte`, `recibiendo_proyectos`, `bienvenida_vista`; migración de datos para los
  usuarios existentes.
- **FR-009**: Personas relacionadas y sugerencias de profesores en servicios con consultas agregadas (sin N+1).
- **FR-010**: `SolicitudRevision` con estados pendiente, aceptada, no aceptada, retirada y reasignada;
  `sugerir_profesores(proyecto, limite=5)` devuelve cada profesor con sus motivos.
- **FR-011**: Todo permiso se comprueba en el servidor según el rol activo y la relación con el proyecto.
- **FR-012**: Íconos SVG guardados en el repo con la etiqueta `{% icono %}` (`aria-hidden` por defecto).
- **FR-013**: Fotos de perfil y portadas: imágenes reales (jpg, png, webp, ≤ 5 MB), convertidas a
  webp en el servidor con nombre aleatorio.
- **FR-014**: Toda cadena nueva traducida al inglés; migraciones reversibles y sin pendientes.

### Key Entities

- **Periodo**: gana `es_actual`; pierde `abierto`.
- **PlanEstudio**: nombre, año, activo; agrupa asignaturas.
- **Asignatura**: gana plan y código; el nombre es único dentro del plan.
- **Perfil**: datos públicos de una persona; aptitudes, experiencias, estudios y asignaturas que imparte.
- **SolicitudRevision**: petición de un proyecto a un profesor, con su respuesta.
- **Proyecto**: gana `periodo_aprobacion`, imagen de portada, color de portada y enlace de video.
- **EventoEstado**: gana `accion` para registrar el flujo de solicitudes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Las 357 pruebas existentes y las nuevas de cada historia pasan.
- **SC-002**: `makemigrations --check` no detecta cambios y los mensajes compilan.
- **SC-003**: Ningún proyecto, autoría, evento, comentario ni guardado se pierde al migrar.
- **SC-004**: Un estudiante envía un proyecto eligiendo revisor en menos de 2 minutos.
- **SC-005**: La página de un perfil y la elección de revisor hacen un número fijo de consultas,
  sin importar cuántos proyectos o profesores haya.

## Assumptions

- La 008 está integrada (comprobado el 2026-11-25).
- El recordatorio al tercer día es opcional y se haría con un comando de gestión programable.
- La lista de profesores es pequeña (decenas): la búsqueda y los filtros de la lista completa se
  hacen en el servidor con recarga parcial sencilla.
- Los íconos de GitHub, LinkedIn y ORCID se toman de Simple Icons (CC0) en una versión que aún los
  incluya; los demás de Tabler Icons (MIT).
