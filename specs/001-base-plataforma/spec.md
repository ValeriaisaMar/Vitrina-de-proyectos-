# Feature Specification: Base de la plataforma

**Feature Branch**: `feature/001-base-plataforma`

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "Dejar lista la base de la Vitrina de Proyectos: configuración desde
.env con PostgreSQL, el usuario propio que usarán los demás módulos, la plantilla base con el
diseño neo-brutalismo institucional de la UTEQ, una portada animada, el cambio de idioma
español/inglés, el modo claro/oscuro y páginas de error con el mismo diseño."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Poner a andar el proyecto en cualquier equipo (Priority: P1)

Un integrante del equipo clona el repositorio, copia `.env.example` a `.env`, escribe los datos
de su PostgreSQL y, siguiendo el README, tiene la plataforma funcionando en su equipo. Las
claves y contraseñas nunca quedan escritas en el código.

**Why this priority**: sin esto nadie del equipo puede probar nada, y el usuario propio debe
existir antes de la primera migración: cambiarlo después obliga a borrar la base de datos.

**Independent Test**: en un clon limpio con PostgreSQL vacío, seguir el README de principio a
fin y abrir la portada sin errores; ejecutar `python manage.py test` en verde.

**Acceptance Scenarios**:

1. **Given** un clon limpio y una base PostgreSQL vacía, **When** el integrante completa `.env`
   y ejecuta las migraciones, **Then** se crean todas las tablas, incluida la del usuario propio,
   sin errores.
2. **Given** que falta una variable obligatoria en `.env`, **When** se inicia el servidor,
   **Then** se muestra un mensaje que dice qué variable falta, en vez de un error confuso.
3. **Given** un admin creado con `createsuperuser`, **When** entra al panel de Django,
   **Then** puede ver y editar usuarios por su correo, nombre y rol.
4. **Given** el repositorio, **When** se busca la clave secreta o contraseñas en el código,
   **Then** no aparece ninguna: todas salen de `.env`.

---

### User Story 2 - Ver una portada que represente a la UTEQ (Priority: P1)

Un visitante entra a la página principal y ve, con la identidad de la UTEQ, de qué trata la
plataforma: un encabezado con el logo y la navegación, una portada con movimiento sutil, los
pasos de cómo funciona, una invitación a crear cuenta y un pie de página. Se ve bien en un
celular, una tablet y un computador.

**Why this priority**: es la primera impresión de la plataforma y la base visual que heredan
todas las demás páginas.

**Independent Test**: abrir `/` en anchos de 360, 768, 1280 y 1920 px y comprobar que todas las
secciones se ven completas, sin desplazamiento horizontal y con la navegación usable.

**Acceptance Scenarios**:

1. **Given** un visitante sin sesión, **When** abre `/`, **Then** ve el encabezado (logo,
   Inicio, Explorar, Verificar QR, selector de idioma, botón de tema, Iniciar sesión y Crear
   cuenta), la portada, la sección "Cómo funciona" con cuatro pasos, la invitación a crear
   cuenta y el pie de página.
2. **Given** una pantalla de 360 px, **When** el visitante abre la página, **Then** la
   navegación se agrupa en un menú desplegable que se abre y se cierra con un botón de al menos
   44 px, y no hay desplazamiento horizontal.
3. **Given** que el sistema del visitante pide reducir el movimiento, **When** abre la portada,
   **Then** no se reproduce ninguna animación y el contenido se ve completo.
4. **Given** que el logo oficial todavía no está en el proyecto, **When** se carga cualquier
   página, **Then** aparece el nombre "Vitrina de Proyectos" en su lugar, sin imágenes rotas.

---

### User Story 3 - Usar la plataforma en español o en inglés (Priority: P1)

Cualquier persona cambia el idioma desde el encabezado. Todos los textos de la interfaz cambian
y la elección se mantiene al navegar y al volver otro día.

**Why this priority**: es un requisito del equipo y es mucho más barato prepararlo en la base
que agregarlo cuando ya existan muchas páginas.

**Independent Test**: en la portada y en las páginas de error, cambiar a inglés y comprobar que
no queda ningún texto de interfaz en español; recargar y comprobar que sigue en inglés.

**Acceptance Scenarios**:

1. **Given** un visitante nuevo, **When** abre la plataforma, **Then** la ve en español.
2. **Given** la portada en español, **When** el visitante elige "EN", **Then** vuelve a la misma
   página con todos los textos de interfaz en inglés.
3. **Given** que eligió inglés, **When** cierra el navegador y vuelve, **Then** la plataforma
   sigue en inglés.
4. **Given** que el selector muestra el idioma activo, **When** se lee con un lector de
   pantalla, **Then** se anuncia cuál está seleccionado.

---

### User Story 4 - Elegir modo claro u oscuro (Priority: P2)

Cualquier persona alterna entre modo claro y oscuro con un botón del encabezado. Por defecto se
sigue la configuración del sistema, y la elección se recuerda.

**Why this priority**: mejora la comodidad y está en los requisitos, pero la plataforma funciona
sin él.

**Independent Test**: alternar el tema, recargar la página y comprobar que se mantiene sin un
destello del otro tema al cargar; verificar el contraste en ambos temas.

**Acceptance Scenarios**:

1. **Given** un sistema en modo oscuro y un visitante nuevo, **When** abre la plataforma,
   **Then** la ve en modo oscuro.
2. **Given** la plataforma en modo claro, **When** el visitante pulsa el botón de tema,
   **Then** cambia a oscuro, el botón actualiza su etiqueta accesible y la elección se recuerda.
3. **Given** un tema elegido, **When** recarga la página, **Then** no se ve ni por un instante
   el otro tema.
4. **Given** cualquiera de los dos temas, **When** se mide el contraste del texto, **Then** es
   de al menos 4.5:1.

---

### User Story 5 - Páginas de error con el mismo diseño (Priority: P3)

Si alguien llega a una dirección que no existe o el servidor falla, ve una página con el diseño
de la plataforma, un mensaje claro y un enlace para volver al inicio.

**Why this priority**: da una imagen profesional, pero no bloquea ninguna otra funcionalidad.

**Independent Test**: con `DEBUG=False`, abrir una URL inexistente y comprobar la página 404 en
ambos idiomas.

**Acceptance Scenarios**:

1. **Given** `DEBUG=False`, **When** se abre una URL inexistente, **Then** aparece la página 404
   con el diseño, el mensaje y un botón "Volver al inicio".
2. **Given** un error interno, **When** se produce, **Then** aparece la página 500 sin mostrar
   detalles técnicos.

---

### Edge Cases

- El navegador tiene JavaScript desactivado: la portada se ve completa en modo claro y el menú
  móvil muestra los enlaces sin necesidad de abrirse.
- El navegador no permite guardar datos locales: el tema sigue al sistema y no aparece ningún
  error.
- Llega un idioma no soportado (por ejemplo, desde la configuración del navegador): se usa
  español.
- La base de datos no está disponible al iniciar: el error dice que revise los datos de
  conexión del `.env`.
- Texto muy largo en inglés: los botones y el menú no se desbordan ni se superponen.

## Requirements *(mandatory)*

### Functional Requirements

**Configuración**

- **FR-001**: El sistema MUST leer de `.env` la clave secreta, el modo de depuración, los hosts
  permitidos, los datos de PostgreSQL y los del correo.
- **FR-002**: El sistema MUST usar PostgreSQL como única base de datos.
- **FR-003**: El repositorio MUST incluir un `.env.example` con todas las variables y sin valores
  reales, y `requirements.txt` en UTF-8 con las dependencias aprobadas y versiones fijas.
- **FR-004**: El sistema MUST crear las cuatro apps (`cuentas`, `proyectos`, `comunidad`,
  `vitrina`) aunque algunas queden vacías hasta su módulo.

**Usuario**

- **FR-005**: El sistema MUST definir un usuario propio en la app `cuentas`, antes de la primera
  migración, que se identifica con su correo (único, sin distinguir mayúsculas), tiene nombres,
  apellidos y un rol (estudiante, profesor o admin; estudiante por defecto).
- **FR-006**: El panel de administración de Django MUST permitir buscar usuarios por correo o
  nombre y cambiar su rol.

**Diseño base**

- **FR-007**: Todas las páginas MUST heredar de una plantilla base con encabezado, área de
  mensajes, contenido y pie de página.
- **FR-008**: La plantilla base MUST cargar un único CSS compilado con Tailwind a partir de un
  tema que define los colores institucionales (`#025a27`, `#ecb932`), los neutros, los colores
  de estado, las fuentes (Unbounded y Archivo) y las variantes de modo oscuro.
- **FR-009**: Las fuentes MUST servirse desde el propio proyecto, sin depender de servicios
  externos.
- **FR-010**: El sistema MUST ofrecer componentes reutilizables de plantilla para botón (primario,
  secundario y peligro), tarjeta, insignia de estado, campo de formulario y aviso.
- **FR-011**: La portada MUST incluir el encabezado, una portada con animación sutil hecha con
  CSS, la sección "Cómo funciona" con cuatro pasos, la invitación a crear cuenta y el pie de
  página, siguiendo el estilo neo-brutalismo institucional de la constitución.
- **FR-012**: Toda animación MUST desactivarse cuando el sistema pide reducir el movimiento.

**Idioma**

- **FR-013**: Todo texto de interfaz MUST estar marcado para traducción y disponible en español
  e inglés; español es el idioma por defecto.
- **FR-014**: El selector de idioma MUST cambiar el idioma sin perder la página actual y
  recordarlo entre visitas.
- **FR-015**: Las traducciones compiladas MUST incluirse en el repositorio.

**Tema**

- **FR-016**: El botón de tema MUST alternar entre claro y oscuro, recordar la elección y, sin
  elección guardada, seguir la configuración del sistema.
- **FR-017**: El tema MUST aplicarse antes de pintar la página, sin destello del otro tema.

**Errores**

- **FR-018**: El sistema MUST mostrar páginas 404 y 500 con el diseño de la plataforma, en el
  idioma activo y sin detalles técnicos.

**Accesibilidad y responsive**

- **FR-019**: Todas las páginas de este módulo MUST funcionar sin desplazamiento horizontal
  entre 360 y 1920 px, con áreas táctiles de al menos 44 px y foco visible al navegar con teclado.
- **FR-020**: El encabezado MUST incluir un enlace "Saltar al contenido" para teclado y lectores
  de pantalla.

### Key Entities

- **Usuario**: persona con cuenta. Correo (identificador único), nombres, apellidos, rol
  (estudiante, profesor o admin), si está activo y fecha de registro. Los módulos siguientes lo
  usan para autoría, revisión y comunidad.
- **Preferencia de idioma**: se guarda en el navegador mediante el mecanismo estándar de
  Django; no es una tabla.
- **Preferencia de tema**: se guarda en el navegador; no es una tabla.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un integrante pasa de un clon limpio a ver la portada en su equipo en menos de
  15 minutos siguiendo solo el README.
- **SC-002**: La portada y las páginas de error se ven completas, sin desplazamiento
  horizontal, en 360, 768, 1280 y 1920 px.
- **SC-003**: Al cambiar a inglés, el 100 % de los textos de interfaz de la portada y de las
  páginas de error cambia de idioma.
- **SC-004**: El contraste de todo el texto es de al menos 4.5:1 en ambos temas.
- **SC-005**: Al recargar, el tema elegido se mantiene sin destello visible.
- **SC-006**: La portada carga en menos de 2 segundos en una red local.
- **SC-007**: `python manage.py test` pasa completo, con pruebas de configuración, usuario,
  idioma, plantillas y páginas de error.

## Assumptions

- El equipo entregará el logo oficial en SVG o PNG; mientras tanto se muestra el nombre de la
  plataforma en texto.
- Las cifras de la portada (proyectos verificados, estudiantes, docentes) y la sección de
  proyectos destacados se agregan en el módulo 003, cuando existan proyectos. El formulario de
  verificación por código se agrega en el módulo 005.
- Los botones "Iniciar sesión" y "Crear cuenta" apuntan a las rutas que completa el módulo 002;
  mientras tanto llevan a las páginas de autenticación que ya existen en el proyecto.
- Unbounded y Archivo tienen licencia SIL Open Font License, que permite incluirlas en el
  proyecto.
- La base de datos SQLite que exista en los equipos no se migra: el módulo arranca con una
  base PostgreSQL vacía.
- La configuración de producción (dominio, HTTPS y servidor) queda fuera de este módulo.
