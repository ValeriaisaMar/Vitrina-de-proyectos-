# Feature Specification: Cuentas y autenticación

**Feature Branch**: `feature/002-cuentas`

**Created**: 2026-11-23

**Status**: Draft

**Input**: User description: "Registro con correos reales verificados por un enlace de activación,
inicio de sesión seguro con límite de intentos, recuperación de contraseña por correo, perfil
del usuario y protección de páginas según el rol (estudiante, profesor, admin)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear una cuenta con un correo real (Priority: P1)

Una persona llena el registro con sus nombres, apellidos, correo y contraseña. La cuenta queda
creada pero inactiva, y le llega un correo con un enlace. Al abrirlo, la cuenta se activa, la
sesión se inicia sola y la persona queda dentro como estudiante.

**Why this priority**: sin cuentas nadie puede subir proyectos ni revisarlos. El enlace es lo que
garantiza que el correo es real.

**Independent Test**: registrarse con un correo nuevo, abrir el enlace que aparece en el correo
(en la terminal si no hay contraseña de aplicación) y comprobar que se entra a la plataforma.

**Acceptance Scenarios**:

1. **Given** un correo que no está registrado, **When** la persona envía el registro completo,
   **Then** se crea la cuenta inactiva con rol estudiante, se envía un correo con el enlace de
   activación y se muestra la página "Revisa tu correo" con la dirección a la que se envió.
2. **Given** un correo ya registrado (con o sin mayúsculas), **When** alguien intenta
   registrarse con él, **Then** el formulario lo rechaza con un mensaje claro.
3. **Given** contraseñas que no coinciden o una contraseña débil, **When** se envía el
   registro, **Then** se rechaza y se explica qué falta.
4. **Given** un enlace de activación válido, **When** se abre, **Then** la cuenta se activa, se
   inicia la sesión y aparece el mensaje "Tu cuenta está activa".
5. **Given** un enlace ya usado, alterado o con más de 24 horas, **When** se abre, **Then** se
   explica que no es válido y se ofrece pedir uno nuevo.
6. **Given** una cuenta todavía inactiva, **When** la persona pide reenviar el enlace con su
   correo, **Then** le llega uno nuevo. La respuesta en pantalla es la misma exista o no la cuenta.

---

### User Story 2 - Iniciar y cerrar sesión de forma segura (Priority: P1)

Una persona con cuenta activa entra con su correo y contraseña. Puede elegir mantener la sesión
abierta. Tras varios intentos fallidos el acceso se bloquea un tiempo. Cierra sesión desde el
encabezado.

**Why this priority**: es la puerta de entrada de estudiantes, profesores y admins.

**Independent Test**: entrar con una cuenta activa; fallar 5 veces y comprobar el bloqueo;
cerrar sesión.

**Acceptance Scenarios**:

1. **Given** una cuenta activa, **When** entra con su correo (en cualquier combinación de
   mayúsculas) y la contraseña correcta, **Then** inicia sesión y vuelve a la página de la que
   venía, o al inicio.
2. **Given** datos incorrectos, **When** intenta entrar, **Then** ve un mensaje que no revela si
   el correo existe.
3. **Given** una cuenta sin activar y la contraseña correcta, **When** intenta entrar, **Then**
   se le dice que active su cuenta y se le ofrece reenviar el enlace.
4. **Given** 5 intentos fallidos con el mismo correo desde la misma dirección IP, **When**
   intenta de nuevo (aunque la contraseña sea correcta), **Then** se le dice que espere 15
   minutos.
5. **Given** que no marcó "Mantener la sesión iniciada", **When** cierra el navegador,
   **Then** la sesión termina.
6. **Given** una sesión iniciada, **When** pulsa "Cerrar sesión", **Then** la sesión termina y
   vuelve al inicio. Cerrar sesión solo funciona por POST.

---

### User Story 3 - Recuperar la contraseña (Priority: P1)

Una persona que olvidó su contraseña escribe su correo, recibe un enlace y elige una
contraseña nueva.

**Why this priority**: sin esto, quien olvida su contraseña queda fuera para siempre.

**Independent Test**: pedir la recuperación, abrir el enlace del correo, poner una contraseña
nueva y entrar con ella.

**Acceptance Scenarios**:

1. **Given** una cuenta activa, **When** pide recuperar la contraseña, **Then** recibe un
   correo con un enlace que vence en 24 horas.
2. **Given** un correo que no existe, **When** pide recuperar, **Then** ve exactamente la misma
   respuesta que si existiera, y no se envía nada.
3. **Given** el enlace válido, **When** escribe una contraseña nueva que cumple las reglas,
   **Then** la contraseña cambia y puede entrar con ella; el enlace deja de servir.

---

### User Story 4 - Ver y editar el perfil (Priority: P2)

Una persona con sesión ve sus datos (nombre, correo, rol, fecha de registro), corrige sus
nombres y apellidos, y cambia su contraseña escribiendo la actual.

**Why this priority**: útil y esperado, pero la plataforma funciona sin él.

**Independent Test**: entrar, cambiar el nombre y la contraseña, y comprobar ambos cambios.

**Acceptance Scenarios**:

1. **Given** una sesión iniciada, **When** abre su perfil, **Then** ve sus datos y su rol.
2. **Given** el perfil, **When** cambia nombres o apellidos, **Then** se guardan y lo confirma
   un mensaje.
3. **Given** la página de cambio de contraseña, **When** escribe la actual correcta y una nueva
   válida, **Then** la contraseña cambia y la sesión sigue abierta.
4. **Given** una persona sin sesión, **When** intenta abrir el perfil, **Then** se le lleva a
   iniciar sesión.

---

### User Story 5 - Páginas protegidas por rol (Priority: P1)

Las páginas de los módulos siguientes (bandeja del profesor, administración) solo se abren con
el rol adecuado. Quien no tiene sesión va al inicio de sesión; quien tiene sesión pero no el
rol ve una página "No tienes permiso".

**Why this priority**: es la base de la seguridad de los módulos 004 a 006.

**Independent Test**: proteger una vista de prueba para profesores y abrirla como visitante,
estudiante y profesor.

**Acceptance Scenarios**:

1. **Given** una vista protegida para profesores, **When** la abre un visitante, **Then** se le
   redirige a iniciar sesión y, al entrar, vuelve a esa vista.
2. **Given** la misma vista, **When** la abre un estudiante, **Then** recibe la página 403 con
   el diseño de la plataforma.
3. **Given** la misma vista, **When** la abre un profesor o un admin, **Then** puede verla.

---

### Edge Cases

- El servidor de correo falla al registrarse: la cuenta se crea igual, se avisa que el correo
  no pudo enviarse y se puede pedir el reenvío.
- Alguien se registra dos veces seguidas con el mismo correo antes de activar: la segunda vez
  se rechaza como correo ya registrado y se le indica que puede reenviar el enlace.
- Una persona ya con sesión abre el registro o el inicio de sesión: se la lleva al inicio.
- Un enlace de activación se abre cuando la cuenta ya está activa: se trata como enlace usado.
- El parámetro `next` apunta a otro sitio: se ignora y se vuelve al inicio.

## Requirements *(mandatory)*

### Functional Requirements

**Registro y activación**

- **FR-001**: El registro MUST pedir nombres, apellidos, correo, contraseña y confirmación.
- **FR-002**: El correo MUST ser único sin distinguir mayúsculas.
- **FR-003**: Las contraseñas MUST pasar los validadores de Django definidos en la constitución.
- **FR-004**: La cuenta nueva MUST quedar inactiva y con rol estudiante.
- **FR-005**: El sistema MUST enviar un correo de activación (texto y HTML, en el idioma activo)
  con un enlace de un solo uso que vence en 24 horas.
- **FR-006**: Abrir un enlace válido MUST activar la cuenta e iniciar la sesión.
- **FR-007**: El sistema MUST permitir reenviar el enlace a cuentas inactivas, respondiendo
  igual exista o no el correo.

**Inicio y cierre de sesión**

- **FR-008**: El inicio de sesión MUST usar correo y contraseña, con la opción "Mantener la
  sesión iniciada" (si no se marca, la sesión termina al cerrar el navegador).
- **FR-009**: Tras 5 intentos fallidos con el mismo correo e IP, el sistema MUST bloquear ese
  correo desde esa IP durante 15 minutos. Un inicio de sesión correcto reinicia el conteo.
- **FR-010**: Una cuenta inactiva con contraseña correcta MUST recibir un mensaje que la invite
  a activar su cuenta y un enlace para reenviar la activación.
- **FR-011**: El cierre de sesión MUST hacerse por POST.
- **FR-012**: Las redirecciones después de iniciar sesión MUST aceptar solo direcciones del
  mismo sitio.

**Recuperación**

- **FR-013**: La recuperación MUST enviar un enlace que vence en 24 horas solo a cuentas
  activas, y responder igual exista o no el correo.
- **FR-014**: El enlace de recuperación MUST permitir fijar una contraseña nueva que cumpla las
  reglas y dejar de servir después de usarse.

**Perfil**

- **FR-015**: Una persona con sesión MUST poder ver su perfil y editar sus nombres y apellidos.
- **FR-016**: Una persona con sesión MUST poder cambiar su contraseña escribiendo la actual.
- **FR-017**: El correo y el rol MUST NOT poder cambiarse desde el perfil.

**Permisos**

- **FR-018**: El sistema MUST ofrecer un decorador `@rol_requerido(...)` que redirija a iniciar
  sesión a quien no tiene sesión y responda 403 a quien no tiene el rol.
- **FR-019**: La página 403 MUST tener el diseño de la plataforma y estar en ambos idiomas.

**Interfaz**

- **FR-020**: Todas las páginas de cuentas MUST seguir el diseño (zona de trabajo: sobria),
  funcionar de 360 a 1920 px, estar en español e inglés y mostrar los errores junto a cada campo.
- **FR-021**: El encabezado MUST mostrar "Iniciar sesión" y "Crear cuenta" a visitantes, y el
  nombre, "Mi perfil" y "Cerrar sesión" a quien tiene sesión.

### Key Entities

- **Usuario** (ya existe, módulo 001): se usan `is_active` para la activación y `rol` para los
  permisos. No se agregan campos.
- **Intentos fallidos**: contador temporal en la caché de Django, por correo e IP. No es una tabla.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona nueva pasa de abrir el registro a tener su cuenta activa en menos de
  3 minutos (sin contar lo que tarda el correo en llegar).
- **SC-002**: El 100 % de los enlaces de activación y recuperación dejan de servir después de
  usarse o a las 24 horas.
- **SC-003**: Ninguna respuesta del registro, del reenvío ni de la recuperación permite saber si
  un correo tiene cuenta, salvo el aviso de correo duplicado del propio registro.
- **SC-004**: El sexto intento tras 5 fallos seguidos se rechaza siempre durante 15 minutos.
- **SC-005**: `python manage.py test` pasa completo, con pruebas de cada escenario de aceptación.

## Assumptions

- El aviso de "correo ya registrado" en el registro revela que la cuenta existe; se acepta
  porque es lo que la persona necesita saber para no duplicar su cuenta, y la recuperación y el
  reenvío siguen sin revelarlo.
- El conteo de intentos usa la caché en memoria de Django. En producción con varios procesos
  conviene una caché compartida (base de datos); eso se configura al desplegar.
- El correo no se puede cambiar desde el perfil, porque requeriría verificar el nuevo; queda
  para una versión posterior. Un admin puede corregirlo desde el panel de Django.
- Después de activar la cuenta se vuelve al inicio; el panel de cada rol llega en el módulo 006.
- La dirección IP se toma de la conexión directa (`REMOTE_ADDR`); si en producción hay un proxy,
  se ajusta al desplegar.
