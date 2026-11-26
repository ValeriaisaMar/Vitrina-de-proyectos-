<!--
Sync Impact Report
Version change: 2.1.0 → 3.0.0 (MAJOR: cambian reglas existentes de revisión, estados y archivos)
Principios modificados:
  III. Entradas no confiables → la foto de perfil y la portada del proyecto admiten hasta 5 MB y se
       reprocesan a webp en el servidor (spec 009). La galería sigue en 3 MB.
  V. Permisos por rol → el creador elige al profesor revisor; solo el profesor asignado revisa y
       decide; el admin reasigna el revisor (ya no decide).
  VII. Estados e historial → mismos seis estados; Enviado → En revisión lo hace el profesor asignado
       (al aceptar la solicitud o al retomar un reenvío). El historial registra también las acciones
       de las solicitudes de revisión.
  X. Interfaz → íconos SVG guardados en el repositorio (sin CDN).
Aprobación: pedida por el equipo en el documento de la spec 009; se confirma al revisar el Pull Request.
Plantillas revisadas: sin cambios de estructura.
Documentos a actualizar: docs/sdd/constitucion.md ✅, README.md ✅.
Pendientes: ninguno.

Historial anterior:
Version change: 2.0.0 → 2.1.0 (MINOR: se amplía la lista de dependencias aprobadas)
Principios modificados:
  XII. Dependencias → se aprueba cryptography (y cffi y pycparser, que instala) para cifrar la
       contraseña del correo de envío que el admin guarda desde la app (spec 008, historia 3).
Aprobación: el equipo la aprobó expresamente el 2026-11-24 al planear la spec 008.
Plantillas revisadas: sin cambios de estructura.
Documentos a actualizar: README.md ✅ (CLAVE_CIFRADO), .env.example ✅, docs/sdd/constitucion.md ✅.
Pendientes: ninguno.

Historial anterior:
Version change: 1.0.0 → 2.0.0 (MAJOR: se retiran y cambian reglas de forma incompatible)
Principios modificados:
  I. Tecnología → ahora define cuatro apps; Docker sale del alcance actual.
  III. Entradas no confiables → agrega validación de archivos subidos.
  IV. Permisos por rol → roles visitante, estudiante, profesor, admin; reglas de coautoría.
  V. Integridad de la verificación → agrega código VP, QR y certificado.
  IX. Plantillas y estilos → pasa a "Interfaz": Tailwind, estilo neo-brutalismo institucional,
      accesibilidad, responsive y modo claro/oscuro.
  XII. Idioma → interfaz bilingüe español/inglés con i18n de Django.
  X. Dependencias → lista de dependencias aprobadas.
Principios añadidos: Autenticación segura; Estados e historial; Código entendible y aprendizaje.
Principios retirados: VI. Health Score; VII. Conservación de datos del Cementerio (fuera de alcance;
  la conservación del historial pasa al principio de Estados e historial).
Secciones modificadas: Restricciones operativas para la IA (bitácora APRENDIZAJE.md).
Plantillas revisadas: plan-template.md (Constitution Check lee esta versión) ✅,
  spec-template.md ✅, tasks-template.md ✅ (sin cambios de estructura).
Documentos a actualizar: README.md ✅, docs/sdd/constitucion.md ✅ (ahora apunta a este archivo).
Pendientes: ninguno.
-->
# Constitución de Vitrina de Proyectos

Vitrina de Proyectos es la plataforma donde los estudiantes de **Ingeniería de Software**
de la **Facultad de Ciencias de la Computación de la UTEQ** publican sus proyectos, los docentes
los revisan y, una vez aprobados, quedan verificados con un código y un QR que cualquiera puede
comprobar. Esta constitución fija las reglas que todo el código y toda especificación deben cumplir.

## Core Principles

### I. Tecnología
El código MUST usar Python 3.12 o superior y Django 6.1, con PostgreSQL como base de datos en
todos los entornos. El proyecto Django se llama `config` y el código se organiza en cuatro apps:

- `cuentas`: usuario, registro, activación, inicio de sesión, recuperación de contraseña y roles.
- `proyectos`: proyectos, coautores, tecnologías, archivos, estados, historial, revisión, QR y certificado.
- `comunidad`: me gusta, favoritos y comentarios.
- `vitrina`: páginas públicas (inicio, explorar, detalle y verificación).

Una app MUST NOT importar vistas de otra; solo modelos, formularios o servicios. Docker queda
fuera del alcance actual y se incorporará mediante una enmienda. La razón: un solo stack,
conocido por todo el equipo, que pueda mantenerse después del curso.

### II. Consultas seguras
Las consultas MUST usar el ORM de Django. MUST NOT escribirse SQL manual ni construirse
consultas con f-strings o concatenación. Las listas MUST evitar consultas repetidas en bucle
usando `select_related` o `prefetch_related` cuando corresponda.

### III. Entradas no confiables
Todo dato recibido de usuarios (formularios, parámetros de URL, enlaces, comentarios y archivos)
MUST tratarse como no confiable:

- Se muestra solo con el escapado automático de las plantillas; `|safe` y `mark_safe` MUST NOT
  usarse sobre contenido de usuarios.
- Los enlaces externos MUST validarse como URL `http` o `https` antes de guardarse.
- Los archivos MUST validarse por extensión, tipo y tamaño: PDF de hasta 10 MB e imágenes
  JPG, PNG o WEBP de hasta 3 MB (galería) o 5 MB (foto de perfil y portada del proyecto). Las
  imágenes MUST abrirse con Pillow para comprobar que son reales. Se guardan en `media/` con
  nombres generados por el sistema; la foto de perfil y la portada se reprocesan a webp.
- Todo formulario que cambia datos MUST usar POST con protección CSRF.

### IV. Autenticación segura
- El usuario MUST iniciar sesión con su correo; el correo es único y no distingue mayúsculas.
- Toda cuenta nueva MUST quedar inactiva hasta que el usuario abra el enlace de activación
  enviado a su correo. Los enlaces de activación y de recuperación MUST usar los generadores de
  tokens de Django y vencer en 24 horas.
- La recuperación de contraseña MUST responder lo mismo exista o no el correo, para no revelar
  qué cuentas existen.
- Las contraseñas MUST pasar los validadores de Django (largo mínimo 8, no comunes, no solo
  números, no parecidas a los datos del usuario).
- Tras 5 intentos fallidos con el mismo correo e IP, el inicio de sesión MUST bloquearse 15 minutos.
- En producción las cookies de sesión y CSRF MUST ser `Secure` y `HttpOnly` cuando aplique.

### V. Permisos por rol
Los roles son visitante (sin cuenta), estudiante, profesor y admin. Toda cuenta nace como
estudiante; solo un admin MUST poder cambiar roles. Cada vista MUST verificar en el servidor el
rol y, cuando aplica, la relación con el objeto:

- Un estudiante MUST editar solo proyectos de los que es autor o coautor, y solo en estado
  Borrador o Con observaciones.
- El creador del proyecto MUST ser el único que elige al profesor revisor, y el profesor elegido
  MUST aceptar la solicitud antes de revisar. Solo el profesor asignado MUST poder aprobar, pedir
  cambios o rechazar ese proyecto. El admin MUST poder reasignar el revisor, pero no decide.
- Solo el autor del proyecto y los admins MUST poder ocultar comentarios.

Ocultar un botón en la plantilla MUST NOT considerarse control de acceso.

### VI. Integridad de la verificación
- Las páginas públicas MUST mostrar únicamente proyectos en estado Aprobado.
- Un proyecto MUST NOT aprobarse sin la decisión explícita de un profesor o admin.
- Al aprobarse, el proyecto MUST recibir un código único con formato `VP-AAAA-NNNN`, que no
  cambia nunca. El QR MUST apuntar a la página pública de verificación de ese código, y el
  certificado PDF MUST incluir el mismo código y QR.
- La página de verificación MUST mostrar solo datos públicos: título, autores, docente que
  aprobó, fecha y código.

### VII. Estados e historial
Los estados son Borrador, Enviado, En revisión, Con observaciones, Aprobado y Rechazado. Las
únicas transiciones permitidas son:

| Desde | Hacia | Quién |
|---|---|---|
| Borrador | Enviado | autor (con un período académico actual definido) |
| Enviado | En revisión | el profesor asignado (al aceptar la solicitud o al retomar un reenvío) |
| En revisión | Aprobado, Con observaciones o Rechazado | el profesor asignado |
| Con observaciones | Enviado | autor (vuelve al mismo profesor) |

Mientras está Enviado, el proyecto espera revisor, espera la aceptación del profesor elegido o
espera que el profesor asignado lo retome; esos subestados se deducen de las solicitudes de
revisión y no son estados nuevos.

Todo cambio de estado MUST pasar por una única función de servicio en
`proyectos/servicios.py`, que valida la transición y el permiso y registra un evento con estado
anterior, estado nuevo, actor, comentario y fecha. Pedir cambios o rechazar MUST exigir un
comentario. Las solicitudes de revisión (solicitada, aceptada, no aceptada, retirada,
reasignada) MUST quedar también en el historial. El historial MUST NOT editarse ni borrarse, y un proyecto que ya salió de Borrador
MUST NOT eliminarse.

### VIII. Pruebas
Toda funcionalidad MUST incluir pruebas automáticas en el paquete `tests/` de su app. Como
mínimo se prueban: cada URL con cada rol (acceso permitido y denegado), cada transición
permitida y prohibida, los flujos de correo (con `mail.outbox`) y las respuestas de archivos
(QR y PDF). `python manage.py test` MUST pasar completo antes de entregar un módulo.

### IX. Código entendible y aprendizaje
El código MUST poder leerlo un estudiante que está aprendiendo Django:

- Se prefiere lo explícito: vistas basadas en funciones, salvo cuando una vista genérica de
  Django (por ejemplo las de recuperación de contraseña) ahorra código sin esconder la lógica.
- La lógica de negocio vive en `servicios.py`, no en plantillas ni repartida entre vistas.
- Cada módulo, clase y función no trivial MUST tener un docstring corto en español que diga qué
  hace y por qué.
- Los nombres de modelos, campos, vistas y URLs MUST estar en español, de forma consistente.
- Cada tarea implementada MUST dejar una entrada en `APRENDIZAJE.md` con qué se hizo, por qué y
  qué concepto de Django se usó.

### X. Interfaz
- Las plantillas MUST heredar de `templates/base.html` y reutilizar los componentes de
  `templates/componentes/`.
- Los estilos MUST usar Tailwind CSS compilado con el ejecutable standalone. Colores, fuentes y
  medidas se definen una sola vez como tema en `static/src/entrada.css`; el resultado compilado
  `static/css/app.css` se sube al repositorio. MUST NOT usarse el CDN de Tailwind.
- Colores institucionales exactos: verde `#025a27` (protagonista) y amarillo `#ecb932` (solo
  acentos: subrayados, calcomanías y foco del teclado; nunca como fondo de secciones grandes).
- Estilo: neo-brutalismo institucional. La parte pública usa bordes de 2 px, sombras sólidas y
  botones que se hunden; los paneles usan bordes sin sombras ni elementos girados; el sello de
  verificación y el certificado son formales y usan solo verde.
- Tipografía: Unbounded para títulos y Archivo para todo lo demás.
- Íconos: SVG guardados en el repositorio (Tabler Icons y logos de Simple Icons), insertados con
  la etiqueta `{% icono %}`; MUST NOT cargarse desde un CDN.
- Accesibilidad: contraste mínimo 4.5:1 en texto, áreas táctiles de 44 px, foco visible,
  etiquetas en todos los campos, y las animaciones MUST respetar `prefers-reduced-motion`.
- Responsive: toda página MUST funcionar sin desplazamiento horizontal desde 360 px hasta 1920 px.
- Tema: modo claro y oscuro; por defecto sigue al sistema y la elección del usuario se recuerda.

### XI. Idioma
La interfaz MUST estar disponible en español (por defecto) e inglés con la internacionalización
de Django. Todo texto visible en plantillas, formularios, mensajes y correos MUST marcarse para
traducción. El contenido escrito por los usuarios no se traduce. Los archivos `.mo` compilados se
suben al repositorio. La documentación y los comentarios del código van en español.

### XII. Dependencias
Las dependencias aprobadas son: Django, psycopg, python-dotenv, qrcode, Pillow, reportlab y
cryptography (para cifrar secretos guardados en la base de datos, spec 008), más las que estas
instalan. Cualquier otra MUST aprobarse expresamente por el equipo antes de
agregarse. `requirements.txt` MUST guardarse en UTF-8 con versiones fijas.

### XIII. Secretos y configuración
Las credenciales y claves (incluida la contraseña de aplicación del correo) MUST vivir en `.env`,
que MUST NOT subirse al repositorio. `.env.example` MUST mantenerse actualizado y sin valores
reales. `settings.py` MUST leer de `.env` la clave secreta, el modo de depuración, los hosts
permitidos, la base de datos y el correo. En producción `DEBUG` MUST ser `False`.

### XIV. Flujo de trabajo
La rama `main` MUST mantenerse estable. Cada módulo se desarrolla en una rama
`feature/NNN-nombre` y se integra mediante Pull Request. Los commits MUST usar los prefijos
`feat:`, `fix:`, `docs:`, `test:`, `style:` o `refactor:`. Los tres integrantes se turnan los
commits para que todos queden en el historial.

### XV. Prioridad del núcleo
Los módulos se construyen en este orden: 001 Base, 002 Cuentas, 003 Proyectos, 004 Revisión e
historial, 005 QR y certificado, 006 Paneles por rol, 007 Comunidad. Un módulo MUST NOT
empezarse si el anterior no pasa sus pruebas. Comunidad es lo único que puede quedar fuera si
falta tiempo.

## Restricciones operativas para la IA

- La IA MUST modificar únicamente los archivos enumerados en el plan de cada funcionalidad.
- La IA MUST NOT borrar ni modificar migraciones existentes; los cambios de modelos MUST
  hacerse con migraciones nuevas.
- La IA MUST NOT ejecutar comandos fuera de la carpeta del proyecto.
- La IA MUST NOT leer, mostrar ni modificar `.env`.
- La IA MUST NOT ejecutar comandos destructivos sobre la base de datos (por ejemplo `flush` o
  borrar tablas) sin confirmación expresa.
- La IA MUST registrar cada tarea en `APRENDIZAJE.md` (principio IX).

## Revisión de cumplimiento

Cada Pull Request MUST comprobar el cumplimiento de los principios aplicables, incluir pruebas
para la funcionalidad nueva y mostrar `python manage.py test` en verde. Las desviaciones
requieren aprobación expresa del equipo y quedar documentadas en el Pull Request.

## Governance

Las enmiendas a esta constitución MUST proponerse mediante Pull Request e incluir la
justificación, el impacto sobre principios y prácticas existentes, y la actualización de versión
y fecha. La integración requiere aprobación expresa del equipo.

El versionado sigue SemVer: MAJOR para retirar o cambiar de forma incompatible una regla; MINOR
para agregar principios o ampliar materialmente las reglas; PATCH para aclaraciones sin cambio
de significado.

Quienes revisen Pull Requests MUST verificar la conformidad con esta constitución. En caso de
conflicto, esta constitución prevalece sobre cualquier práctica local hasta que se apruebe una
enmienda.

**Version**: 3.0.0 | **Ratified**: 2026-11-22 | **Last Amended**: 2026-11-25
