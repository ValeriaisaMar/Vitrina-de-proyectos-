# Feature Specification: Proyectos, explorar y detalle

**Feature Branch**: `feature/003-proyectos`

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "Los estudiantes crean y editan sus proyectos (uno o varios autores con
cuenta, asignatura de la malla de Ingeniería de Software de la UTEQ, periodo, tecnologías,
repositorio, demo, imágenes y PDF). Cualquier persona explora los proyectos aprobados con
búsqueda y filtros y ve su detalle. La portada muestra cifras y proyectos destacados."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear un proyecto (Priority: P1)

Un estudiante con cuenta activa crea un proyecto: título, resumen, descripción, asignatura,
periodo, tecnologías, enlace al repositorio, demo opcional, hasta 4 imágenes y un PDF opcional.
Puede agregar coautores escribiendo sus correos. El proyecto queda en Borrador.

**Why this priority**: es el corazón de la plataforma; sin proyectos no hay nada que revisar ni mostrar.

**Independent Test**: entrar como estudiante, crear un proyecto completo con un coautor y verlo
en "Mis proyectos" en estado Borrador.

**Acceptance Scenarios**:

1. **Given** un estudiante con sesión, **When** envía el formulario completo, **Then** se crea
   el proyecto en Borrador, él queda como creador y aparece en "Mis proyectos".
2. **Given** correos de coautores que tienen cuenta activa de estudiante, **When** los agrega,
   **Then** quedan como autores y también ven el proyecto en "Mis proyectos".
3. **Given** un correo de coautor sin cuenta, inactivo o que no es de estudiante, **When** lo
   agrega, **Then** el formulario lo rechaza diciendo cuál correo falla.
4. **Given** un PDF de más de 10 MB, un archivo que no es PDF o una imagen de más de 3 MB,
   **When** se envía, **Then** se rechaza con un mensaje claro.
5. **Given** un enlace que no empieza por `http://` o `https://`, **When** se envía, **Then**
   se rechaza.
6. **Given** un profesor, un admin o un visitante, **When** intenta crear un proyecto,
   **Then** no puede (403 o inicio de sesión).

---

### User Story 2 - Editar o eliminar un proyecto propio (Priority: P1)

Cualquier autor edita el proyecto mientras está en Borrador o Con observaciones: cambia datos,
agrega o quita imágenes, reemplaza el PDF y ajusta los coautores. El creador puede eliminar un
proyecto que nunca salió de Borrador.

**Why this priority**: los proyectos se corrigen según las observaciones del docente (módulo 004).

**Independent Test**: editar un proyecto en Borrador, quitar una imagen y cambiar un coautor;
intentar editar uno aprobado y comprobar que no se puede.

**Acceptance Scenarios**:

1. **Given** un autor y un proyecto en Borrador o Con observaciones, **When** guarda cambios,
   **Then** se guardan y ve un mensaje de confirmación.
2. **Given** un proyecto en Enviado, En revisión, Aprobado o Rechazado, **When** un autor
   intenta editarlo, **Then** recibe 403.
3. **Given** un estudiante que no es autor, **When** intenta editar, **Then** recibe 403.
4. **Given** el creador y un proyecto en Borrador, **When** confirma eliminarlo, **Then** se
   borra con sus archivos. En cualquier otro estado, o si no es el creador, no puede.
5. **Given** la edición, **When** el creador quita a un coautor, **Then** ese coautor deja de
   ver el proyecto; el creador no puede quitarse a sí mismo.

---

### User Story 3 - Explorar los proyectos aprobados (Priority: P1)

Cualquier persona, con o sin cuenta, ve los proyectos aprobados en tarjetas. Busca por texto
(título, resumen, tecnología o autor), filtra por tecnología, asignatura y periodo, ordena por
más recientes o por nombre, y pagina de 12 en 12.

**Why this priority**: es la vitrina pública, la razón de ser del proyecto.

**Independent Test**: con proyectos aprobados y no aprobados en la base, abrir Explorar,
buscar, filtrar y comprobar que solo aparecen aprobados.

**Acceptance Scenarios**:

1. **Given** proyectos en distintos estados, **When** un visitante abre Explorar, **Then** solo
   ve los aprobados, con su número total.
2. **Given** una búsqueda, **When** coincide con título, resumen, tecnología o nombre de un
   autor, **Then** el proyecto aparece; si no, no.
3. **Given** filtros de tecnología, asignatura o periodo, **When** se aplican, **Then** la lista
   se reduce y los filtros activos se muestran con la opción de quitarlos.
4. **Given** más de 12 resultados, **When** se pasa de página, **Then** se conservan la
   búsqueda y los filtros.
5. **Given** que no hay resultados, **When** se busca, **Then** aparece un mensaje que invita a
   cambiar los filtros.

---

### User Story 4 - Ver el detalle de un proyecto (Priority: P1)

Cualquier persona abre un proyecto aprobado y ve su galería, descripción, tecnologías,
enlaces, PDF, autores, asignatura y periodo. Los autores, profesores y admins también pueden
abrir proyectos no aprobados como vista previa; para los demás esos proyectos no existen.

**Why this priority**: es lo que se comparte con el QR (módulo 005).

**Independent Test**: abrir un proyecto aprobado sin sesión; abrir uno en Borrador sin sesión
(404) y como autor (vista previa).

**Acceptance Scenarios**:

1. **Given** un proyecto aprobado, **When** un visitante lo abre, **Then** ve toda su información.
2. **Given** un proyecto no aprobado, **When** lo abre un visitante o un estudiante que no es
   autor, **Then** recibe 404.
3. **Given** un proyecto no aprobado, **When** lo abre un autor, un profesor o un admin,
   **Then** lo ve con un aviso de "vista previa" y su estado.

---

### User Story 5 - Portada con datos reales (Priority: P2)

La portada muestra cuántos proyectos verificados hay, cuántos estudiantes son autores y
cuántas tecnologías se usan, y los 3 proyectos aprobados más recientes.

**Why this priority**: completa la portada del módulo 001; no bloquea nada.

**Independent Test**: aprobar 4 proyectos desde el admin y comprobar las cifras y que aparecen
los 3 más recientes.

**Acceptance Scenarios**:

1. **Given** proyectos aprobados, **When** se abre el inicio, **Then** las cifras coinciden con
   la base de datos y se ven los 3 más recientes.
2. **Given** que no hay proyectos aprobados, **When** se abre el inicio, **Then** no se muestran
   cifras en cero ni una sección vacía, sino una invitación a subir el primero.

---

### Edge Cases

- Un coautor escrito dos veces o el propio creador en la lista: se ignora el duplicado.
- Más de 6 autores en total: se rechaza.
- Más de 4 imágenes entre las que ya tiene y las nuevas: se rechaza.
- Dos proyectos con el mismo título: cada uno recibe una dirección (slug) distinta.
- Una asignatura o tecnología desactivada por el admin: deja de aparecer en el formulario,
  pero los proyectos que ya la tienen la conservan.
- Un parámetro de filtro inválido en la URL (por ejemplo `?pagina=abc`): se ignora sin error.

## Requirements *(mandatory)*

### Functional Requirements

**Datos**

- **FR-001**: Cada proyecto MUST tener título (máx. 120), resumen (máx. 300), descripción,
  asignatura, periodo (`AAAA-1` o `AAAA-2`), entre 1 y 8 tecnologías y enlace al repositorio.
  Demo, imágenes y PDF son opcionales.
- **FR-002**: El sistema MUST cargar como datos iniciales las asignaturas de la malla de
  Ingeniería de Software de la UTEQ (semestres I a X, sin los niveles de inglés) y una lista
  inicial de tecnologías. El admin puede agregar, editar o desactivar ambas.
- **FR-003**: Un proyecto MUST tener entre 1 y 6 autores, todos con cuenta activa de estudiante;
  uno de ellos es el creador.
- **FR-004**: Los enlaces MUST ser `http` o `https`. El PDF MUST pesar hasta 10 MB y ser un PDF
  real; cada imagen hasta 3 MB, en JPG, PNG o WEBP, máximo 4 por proyecto.
- **FR-005**: Los archivos MUST guardarse con nombres generados por el sistema.
- **FR-006**: Cada proyecto MUST tener una dirección legible y única (slug) que no cambia aunque
  se edite el título.

**Permisos**

- **FR-007**: Solo estudiantes MUST poder crear proyectos.
- **FR-008**: Solo los autores MUST poder editar, y solo en Borrador o Con observaciones.
- **FR-009**: Solo el creador MUST poder eliminar, y solo en Borrador.
- **FR-010**: Las páginas públicas MUST mostrar solo proyectos aprobados; los no aprobados
  responden 404 salvo a autores, profesores y admins (vista previa).

**Explorar y detalle**

- **FR-011**: Explorar MUST permitir búsqueda de texto, filtros por tecnología (varias),
  asignatura y periodo, orden por recientes o por título, y paginación de 12 conservando filtros.
- **FR-012**: Explorar MUST mostrar cuántos proyectos aprobados usan cada tecnología.
- **FR-013**: El detalle MUST mostrar galería, descripción, tecnologías, enlaces, PDF, autores,
  asignatura y periodo.

**Mis proyectos y portada**

- **FR-014**: Cada estudiante MUST tener una página "Mis proyectos" con sus proyectos, estado y
  acciones disponibles. (El panel completo llega en el módulo 006.)
- **FR-015**: La portada MUST mostrar las cifras y los 3 proyectos aprobados más recientes, o una
  invitación si aún no hay ninguno.

**Interfaz**

- **FR-016**: Todas las páginas MUST seguir el diseño (pública expresiva; formularios y tablas
  sobrios), funcionar de 360 a 1920 px y estar en español e inglés.

### Key Entities

- **Asignatura**: nombre y semestre (1 a 10) de la malla; activa o no.
- **Tecnología**: nombre único; activa o no.
- **Proyecto**: título, slug, resumen, descripción, asignatura, periodo, tecnologías,
  repositorio, demo, PDF, estado, fechas de creación, actualización y aprobación. Incluye
  desde ya los campos `codigo` y `revisor`, que llenan los módulos 004 y 005.
- **Autoría**: une a un usuario con un proyecto y marca al creador.
- **Imagen**: archivo y orden dentro de la galería de un proyecto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un estudiante crea un proyecto completo en menos de 5 minutos.
- **SC-002**: El 100 % de los proyectos no aprobados quedan fuera de Explorar, de la portada y
  del detalle público.
- **SC-003**: Explorar responde en menos de 1 segundo con 200 proyectos en una red local.
- **SC-004**: `python manage.py test` pasa completo, con pruebas de cada escenario.

## Assumptions

- La malla se tomó del sitio oficial de la UTEQ (imagen "Malla curricular Software"): 53
  asignaturas de los semestres I a X. Los niveles de inglés no se incluyen porque no generan
  proyectos de software. El admin puede ajustarla.
- Enviar a revisión, la bandeja y el historial llegan en el módulo 004; el código, QR y
  certificado en el 005. Por eso, para la demostración, un admin puede aprobar un proyecto
  desde el panel de Django.
- Los coautores se agregan por correo; no reciben notificación en este módulo.
