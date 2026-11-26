# Feature Specification: Configuración inicial — crear el primer admin desde la app

**Feature Branch**: `feat/010-primer-admin`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Una forma de crear el primer administrador desde el navegador para que,
al desplegar en un servidor nuevo con la base de datos vacía, no haga falta `createsuperuser`. No es
automática: se llega desde un enlace discreto en Entrar que solo existe mientras no hay un admin
activo; está protegida con un código de un solo uso que solo ve quien tiene acceso al servidor
(comando de gestión o logs)." (documento `spec-010-configuracion-inicial-admin.md`, historias 1 a 4,
todas obligatorias).

## Clarifications

### Session 2026-11-26

Decisiones tomadas al especificar (sin preguntas abiertas; se pueden corregir antes del plan):

- Q: La constitución (principio IV) exige que toda cuenta nueva quede inactiva hasta abrir el enlace
  de activación, y (principio V) que solo un admin cambie roles. El primer admin nace activo y sin
  que otro admin le dé el rol. → A: Es una **excepción acotada a la configuración inicial** (y al
  camino por consola `createsuperuser`), que solo existe mientras no hay un admin activo y exige un
  código que solo ve quien tiene acceso al servidor. Se enmienda la constitución a **3.1.0** (MINOR:
  amplía reglas) en esta misma rama; el equipo la aprueba al revisar el Pull Request.
- Q: "Correo marcado como verificado": el usuario no tiene un campo aparte de verificación. → A: En
  este proyecto la cuenta activa **es** la cuenta con correo verificado (la activación por enlace es
  la verificación). Dejar la cuenta activa cumple el requisito; no se agrega un campo nuevo.
- Q: La constitución deja Docker fuera del alcance. → A: No se agregan archivos de Docker. El README
  solo **menciona** el comando con `docker compose exec …` como ejemplo para quien despliegue con
  Docker, junto al equivalente sin Docker.
- Q: La caché actual vive en la memoria de cada proceso; con varios procesos del servidor, borrar la
  caché en uno no la borra en los demás. → A: La caché solo decide si **se muestra el enlace** en
  Entrar y además vence sola en poco tiempo (1 minuto). La página de configuración y todo el proceso
  de creación consultan siempre la base de datos, así que un enlace que se muestre unos segundos de
  más no abre nada: lleva a un 404.
- Q: "Usar una cuenta que ya existe" con una cuenta que nunca se activó. → A: Se permite (el código
  prueba el acceso al servidor y la contraseña prueba que es su cuenta); la cuenta queda activa.
- Q: ¿El código vigente se invalida al generar uno nuevo desde la página (respaldo por logs)? → A:
  La página solo genera un código si **no hay uno vigente**; si ya hay uno, no lo cambia (así recargar
  la página no invalida el código que alguien acaba de copiar). El comando sí reemplaza siempre el
  anterior.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Código de configuración de un solo uso y logs por consola (Priority: P1)

Quien administra el servidor obtiene un código de configuración temporal desde la terminal (comando
de gestión) o, como respaldo, desde los logs de la aplicación, que también salen por consola en
producción.

**Why this priority**: sin el código nadie puede usar la configuración inicial; es la protección
que impide que un desconocido se adueñe de una instalación publicada sin admin.

**Independent Test**: con la base sin admin, correr el comando y ver el bloque con el código en la
terminal; correrlo otra vez y comprobar que el primer código ya no sirve; abrir la página sin código
vigente y ver el bloque en el log, también con el modo de depuración apagado.

**Acceptance Scenarios**:

1. **Given** que no hay admin activo, **When** se corre el comando del código, **Then** la terminal
   muestra un bloque visible con el título "VITRINA: CÓDIGO DE CONFIGURACIÓN INICIAL", el código en
   tres grupos de 4 caracteres, el aviso de que vence en 30 minutos y la dirección de la página de
   configuración (con la URL del sitio si está configurada, si no solo la ruta).
2. **Given** un código generado antes, **When** se corre el comando de nuevo, **Then** el código
   anterior deja de servir y solo vale el nuevo.
3. **Given** que ya hay un admin activo, **When** se corre el comando, **Then** dice que ya existe un
   administrador, no genera nada y termina con error (código de salida distinto de 0).
4. **Given** que no hay admin activo ni código vigente, **When** alguien abre la página de
   configuración, **Then** el servidor genera un código y escribe el mismo bloque en el log como
   advertencia; la página nunca muestra el código y solo indica dónde buscarlo.
5. **Given** el servidor en modo producción (sin depuración), **Then** los avisos de la aplicación y
   el bloque del código salen por la consola del proceso (lo que guardan Docker, systemd o la consola
   de desarrollo), con fecha, nivel y origen.
6. **Given** un código, **When** pasan 30 minutos, se usa una vez con éxito o se termina la
   configuración, **Then** ese código deja de servir.
7. **Given** cualquier log de la aplicación (correo, autenticación, este flujo), **Then** nunca
   contiene contraseñas, códigos introducidos por el usuario ni la contraseña de aplicación del correo.

---

### User Story 2 - Enlace discreto en "Entrar" (Priority: P1)

Mientras no haya un admin activo, la página de Entrar muestra, debajo del formulario, un enlace
pequeño "¿Instalación nueva? Configurar la administración" que lleva a la configuración inicial.

**Why this priority**: es la forma normal de llegar a la configuración; sin él habría que conocer la
dirección de memoria.

**Independent Test**: con la base sin admin, abrir Entrar y ver el enlace; crear el primer admin y
ver que desaparece de inmediato.

**Acceptance Scenarios**:

1. **Given** que no hay admin activo, **When** se abre Entrar, **Then** debajo de "¿Olvidaste tu
   contraseña?" y "Registrarse", separado por una línea fina, aparece el enlace en texto pequeño y
   tono secundario, con un ícono de engranaje o llave, sin aspecto de botón ni color de acento.
2. **Given** que ya hay un admin activo, **Then** el enlace no aparece y la dirección de la
   configuración responde "no encontrado".
3. **Given** que se acaba de crear el primer admin, **When** se vuelve a abrir Entrar, **Then** el
   enlace ya no aparece (no queda un valor viejo guardado).
4. **Given** cualquier otra página (registro, portada, barra superior, pie), **Then** el enlace no
   aparece en ninguna.
5. **Given** un celular de 360 px, el modo oscuro o la navegación con teclado, **Then** el enlace se
   lee bien, tiene foco visible y se puede activar.

---

### User Story 3 - Asistente para crear el primer admin (Priority: P1)

Un visitante con el código abre la configuración inicial, lo introduce y crea una cuenta de admin
nueva o promueve a admin una cuenta que ya existe; al terminar queda dentro como admin.

**Why this priority**: es el objetivo de la funcionalidad: dejar la instalación administrable sin
tocar la consola de Django.

**Independent Test**: con la base vacía y un código vigente, completar el asistente con una cuenta
nueva y comprobar que se entra al panel del admin; repetir con una cuenta de estudiante existente y
comprobar que conserva su rol de estudiante.

**Acceptance Scenarios**:

1. **Given** que no hay admin activo y no hay sesión iniciada, **When** se abre la configuración,
   **Then** se ve un asistente con el sello de la Carrera, dos pasos (código; datos del admin), una
   ayuda plegable "¿Dónde encuentro el código?" con el comando para servidor con Docker, servidor sin
   Docker y desarrollo local, y un enlace "Volver a Entrar".
2. **Given** la pestaña "Crear una cuenta nueva" con código válido, nombres, apellidos, correo y
   contraseña confirmada que cumple las reglas de contraseña, **When** se envía, **Then** se crea la
   cuenta activa, sin correo de activación, con el rol admin asignado "por el sistema" y el motivo
   "Configuración inicial" en el registro de cambios de roles.
3. **Given** la pestaña "Usar una cuenta que ya existe" con código válido y el correo y la
   contraseña correctos de una cuenta registrada, **When** se envía, **Then** la cuenta recibe el rol
   admin además de los que ya tenía y queda activa.
4. **Given** que el proceso termina bien, **Then** se inicia sesión automáticamente con el rol admin
   como rol activo, se llega al panel del admin con el mensaje "Listo. Ya eres administrador de la
   Vitrina." y una lista corta de siguientes pasos con enlaces (configurar el correo de envío, crear
   el período actual, cargar el plan de estudios); el log registra que se completó la configuración
   y con qué correo, sin datos sensibles.
5. **Given** que el proceso ya terminó, **Then** la configuración responde "no encontrado", el
   enlace de Entrar desaparece y el código usado ya no sirve.
6. **Given** un código erróneo, vencido o ya usado, o una cuenta existente con contraseña
   incorrecta o un correo que no existe, **Then** se muestra el mismo tipo de mensaje genérico, sin
   revelar si el correo existe ni cuál dato falló.
7. **Given** 5 códigos erróneos seguidos, **Then** el código vigente se invalida, hay que generar
   otro y el log lo avisa como advertencia; además, demasiados intentos desde la misma dirección IP
   se bloquean por un tiempo.
8. **Given** dos envíos correctos casi simultáneos, **Then** solo uno crea el admin; el otro recibe
   la respuesta de que la configuración ya no está disponible.
9. **Given** una sesión iniciada, **When** se abre la configuración, **Then** se pide cerrar sesión
   antes de continuar.
10. **Given** un usuario que solo tiene el rol admin, **Then** no tiene perfil público (regla de la 009).
11. **Given** la creación del admin por consola (`createsuperuser`), **Then** sigue funcionando y
    también deja "Configuración inicial" en el registro de roles, invalida el código pendiente y
    oculta el enlace de Entrar.

---

### User Story 4 - Qué pasa si se quedan sin admin (Priority: P2)

El último admin activo no puede quedarse sin rol, desactivarse ni borrarse, ni desde la app ni desde
el panel de Django. Si aun así no queda ningún admin activo, la configuración inicial vuelve a estar
disponible, siempre con un código nuevo.

**Why this priority**: evita que la configuración inicial se reabra por accidente y documenta cómo
recuperar el acceso si pasa.

**Independent Test**: con un solo admin, intentar desactivarlo y borrarlo en la app y en el panel de
Django y ver que se bloquea; quitarlo directamente en la base y ver que el enlace reaparece y la
página exige un código nuevo.

**Acceptance Scenarios**:

1. **Given** un único admin activo, **When** alguien intenta quitarle el rol admin, desactivarlo o
   borrarlo (en la app o en el panel de Django), **Then** la acción se rechaza con un mensaje claro y
   nada cambia.
2. **Given** que no queda ningún admin activo (por ejemplo, se cambió directamente en la base de
   datos), **Then** el enlace de Entrar reaparece y la configuración exige un código generado después
   de ese momento; un código anterior (ya usado) no sirve.
3. **Given** el README, **Then** tiene una sección "Recuperar el acceso de administrador" que explica
   este caso.

---

### Edge Cases

- Varios admins activos y se desactiva uno: se permite (no es el último).
- Un admin desactivado no cuenta como admin activo: si es el único, la configuración está disponible.
- Recargar la página de configuración con un código vigente no genera otro ni lo cambia.
- El código se escribe con minúsculas, espacios o sin guiones: se acepta igual.
- El código introducido usa letras confundibles que no existen en el alfabeto (0, O, 1, I, L): es un
  código erróneo como cualquier otro.
- El correo de la cuenta nueva ya está registrado: se indica que use la pestaña de cuenta existente
  (el visitante ya probó tener el código, así que no se filtra información a un desconocido).
- El código vence mientras se llena el formulario: error genérico; hay que generar otro.
- El bloqueo por IP también aplica a quien prueba contraseñas de cuentas existentes.
- Base de datos totalmente vacía (sin períodos, plan ni correo): el panel del admin funciona y los
  siguientes pasos llevan a configurarlos.
- Idioma inglés: toda la página, los mensajes y el bloque de la terminal en la interfaz están
  traducidos (el bloque del log y de la terminal puede quedar en español, es para quien opera el
  servidor).

## Requirements *(mandatory)*

### Functional Requirements

**Código y logs (Historia 1)**

- **FR-001**: El sistema MUST ofrecer un comando de gestión que, si no hay admin activo, invalide el
  código anterior, genere uno nuevo y lo imprima en la terminal en un bloque visible con el código, su
  vencimiento (30 minutos) y la dirección de la configuración; si hay admin activo MUST decirlo y
  terminar con error sin generar nada.
- **FR-002**: Al abrir la configuración sin código vigente y sin admin activo, el sistema MUST generar
  un código y escribir el mismo bloque en el log como advertencia, desde el origen "configuración
  inicial" de cuentas. Si ya hay un código vigente MUST NOT reemplazarlo.
- **FR-003**: El código MUST tener 12 caracteres aleatorios criptográficamente seguros de un alfabeto
  sin caracteres confundibles (sin 0, O, 1, I, L), mostrarse en grupos de 4, y al validarse MUST
  ignorar guiones, espacios y mayúsculas/minúsculas.
- **FR-004**: El sistema MUST guardar solo una huella (hash) del código, nunca el código en claro; el
  código MUST vencer a los 30 minutos, servir una sola vez e invalidarse al crearse el admin.
- **FR-005**: La página de configuración MUST NOT mostrar el código; solo indica que se copie del
  comando en el servidor o de los logs.
- **FR-006**: Los mensajes de la aplicación (origen "cuentas", nivel informativo y superior) y los de
  Django MUST salir por la consola del proceso también con la depuración apagada, con fecha, nivel y
  origen. El nivel de los mensajes de Django MUST poder ajustarse con una variable de entorno
  (`NIVEL_LOG_DJANGO`, por defecto informativo), documentada en `.env.example` y el README, sin
  romper el envío de errores a los administradores si existe.
- **FR-007**: Ningún log MUST contener contraseñas, códigos introducidos ni la contraseña de
  aplicación del correo.

**Enlace en Entrar (Historia 2)**

- **FR-008**: Mientras no haya admin activo, la página de Entrar MUST mostrar, después de los enlaces
  existentes y separado por una línea fina, el enlace discreto "¿Instalación nueva? Configurar la
  administración" hacia la configuración; con admin activo MUST NOT mostrarse. MUST NOT aparecer en
  ninguna otra página.
- **FR-009**: Saber si hay admin activo para mostrar el enlace MUST NOT consultar la base de datos en
  cada visita: el valor se guarda temporalmente y se descarta al dar o quitar el rol admin, al
  activar, desactivar o borrar usuarios y al terminar la configuración inicial.
- **FR-010**: "Admin activo" MUST significar una cuenta activa que tiene el rol admin asignado, y
  MUST calcularse en un único lugar que usan la página, el comando, el enlace y las pruebas.

**Asistente (Historia 3)**

- **FR-011**: La configuración MUST responder "no encontrado" (no "prohibido") cuando hay un admin
  activo. Para visitantes sin admin activo MUST mostrar el asistente en dos pasos; con sesión iniciada
  MUST pedir cerrar sesión.
- **FR-012**: El asistente MUST ofrecer dos opciones en pestañas: crear una cuenta nueva (nombres,
  apellidos, correo, contraseña con confirmación y las reglas de contraseña) o usar una cuenta
  existente (correo y contraseña), a la que se le agrega el rol admin conservando los que tenga.
- **FR-013**: Al terminar, la cuenta MUST quedar activa sin enviar correo de activación, con el rol
  admin asignado por el sistema (sin admin que lo asigne) y una entrada con motivo "Configuración
  inicial" en el registro de cambios de roles; el log MUST registrar la configuración completada y el
  correo, sin datos sensibles.
- **FR-014**: Al terminar, el sistema MUST iniciar sesión con el rol admin como rol activo y llevar
  al panel del admin con el mensaje "Listo. Ya eres administrador de la Vitrina." y los siguientes
  pasos con enlaces: correo de envío, período actual y plan de estudios.
- **FR-015**: Crear o promover el primer admin MUST ser atómico: bloquear el registro de la
  configuración, volver a comprobar que no hay admin activo dentro del mismo bloque y hacer todo o
  nada, de modo que dos envíos simultáneos creen un solo admin.
- **FR-016**: El sistema MUST limitar los intentos por dirección IP y, a los 5 códigos erróneos,
  invalidar el código vigente y avisar en el log como advertencia.
- **FR-017**: Un código malo (erróneo, vencido o usado) y una cuenta existente con datos incorrectos
  MUST dar el mismo tipo de mensaje genérico, sin revelar si el correo existe.
- **FR-018**: La página MUST usar protección CSRF y funcionar para visitantes con todos los
  intermediarios de petición activos (incluido el de rol activo).
- **FR-019**: La creación por consola (`createsuperuser`) MUST seguir funcionando y además dejar el
  motivo "Configuración inicial" en el registro de roles, invalidar el código pendiente y descartar el
  valor guardado del enlace.

**Sin admin (Historia 4)**

- **FR-020**: El sistema MUST impedir quitar el rol admin, desactivar o borrar al último admin activo,
  tanto en la app como en el panel de Django.
- **FR-021**: Si no queda ningún admin activo, el enlace y la configuración MUST volver a estar
  disponibles, siempre con un código nuevo (los códigos usados nunca vuelven a servir).

**Generales**

- **FR-022**: Todo texto visible nuevo MUST estar en español e inglés; la interfaz MUST seguir el
  estilo actual, funcionar desde 360 px sin desplazamiento horizontal, en modo claro y oscuro, y con
  teclado.
- **FR-023**: Las migraciones MUST ser reversibles y MUST NOT borrar ni modificar datos existentes de
  usuarios o proyectos.
- **FR-024**: El README MUST tener las secciones "Primer arranque" (camino por servidor, respaldo
  por logs, alternativa `createsuperuser`, variable `NIVEL_LOG_DJANGO`) y "Recuperar el acceso de
  administrador".

### Key Entities

- **Configuración inicial**: registro único que guarda el estado del proceso: huella del código
  vigente, cuándo se creó, cuándo vence, intentos fallidos con ese código y cuándo se completó la
  configuración. No guarda el código en claro.
- **Rol asignado** (existente): se le agrega el rol admin al primer admin, sin "asignado por".
- **Cambio de rol** (existente): registro de cambios de roles; la entrada del primer admin lleva el
  motivo "Configuración inicial".
- **Usuario** (existente): la cuenta creada o promovida; queda activa.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un servidor recién desplegado, una persona con acceso por terminal deja la
  instalación con su primer admin en menos de 5 minutos, sin usar la consola de Django.
- **SC-002**: Sin el código, el 100 % de los intentos de crear un admin fallan; con un código
  vencido, usado o invalidado tras 5 errores, también.
- **SC-003**: Con un admin activo, la configuración responde "no encontrado" en el 100 % de los
  casos y el enlace no aparece en Entrar.
- **SC-004**: Dos envíos simultáneos del asistente nunca terminan con dos admins.
- **SC-005**: El código nunca aparece en ninguna página ni en ningún mensaje de error; solo en la
  terminal del comando y en el log del servidor.
- **SC-006**: Con la depuración apagada, el bloque del código aparece en la consola del proceso en el
  100 % de las veces que se genera desde la página.
- **SC-007**: Todas las pruebas que pasaban antes (482) siguen pasando, junto con las nuevas.

## Assumptions

- La 008 (`RolAsignado`, `CambioRol` con motivo, regla del último admin al quitar el rol, rol activo
  por middleware) y la 009 (`Perfil`, menú del avatar, etiqueta `{% icono %}`) están en `main`
  (comprobado: PR #14).
- La URL del sitio para el bloque sale de la misma configuración que usan hoy los correos; si no hay,
  se muestra solo la ruta `/configuracion-inicial/`.
- El límite por IP reutiliza el mecanismo existente de intentos de inicio de sesión.
- La caché es la configurada hoy (memoria del proceso); por eso vence sola en 1 minuto y nunca es la
  que decide el acceso (ver Clarifications).
- La sección de siguientes pasos enlaza a las páginas que ya existen para correo de envío, períodos y
  plan de estudios.
- Este trabajo incluye además las correcciones locales del 26 de noviembre que ya estaban en el árbol
  de trabajo (decisión del usuario: van en el mismo PR).
- Commits: los hace el equipo a mano (memoria del proyecto); al terminar cada historia se propone el
  mensaje.
