# Bitácora de aprendizaje

Cada tarea implementada deja aquí qué se hizo, por qué y qué concepto de Django (o de la web)
se usó (constitución, principio IX). La idea es que cualquiera del equipo pueda leer esto y
entender el código sin haberlo escrito.

---

## Módulo 001 · Base de la plataforma

### T001 · `requirements.txt` en UTF-8
**Qué:** se reescribió el archivo con las dependencias aprobadas y versiones fijas.
**Por qué:** el archivo anterior se había generado con `pip freeze > requirements.txt` en
PowerShell, que guarda en UTF-16. Algunas herramientas no lo leen bien.
**Concepto:** fijar versiones (`Django==6.1.3`) hace que todos instalen exactamente lo mismo.
En PowerShell, para generarlo bien: `pip freeze | Out-File -Encoding utf8 requirements.txt`.

### T002 · `.env.example` y `.gitignore`
**Qué:** una plantilla con todas las variables y sin valores reales; `.gitignore` ahora ignora
`.env`, `media/`, `staticfiles/` y el ejecutable de Tailwind.
**Concepto:** los secretos nunca van al repositorio. Cada quien copia `.env.example` como `.env`
y pone sus datos.

### T003 · Las apps `cuentas`, `proyectos` y `comunidad`
**Qué:** se crearon con `django-admin startapp` y se registraron en `INSTALLED_APPS`.
**Concepto:** una *app* es una carpeta con una sola responsabilidad (sus modelos, vistas, URLs,
plantillas y pruebas). Las pruebas van en un paquete `tests/` para poder tener varios archivos.

### T004 · `config/entorno.py`
**Qué:** funciones `variable()`, `booleano()` y `lista()` para leer el `.env`.
**Por qué:** si falta una variable, Django se detiene con un mensaje claro
(*"Falta la variable DB_NAME en el archivo .env"*) en lugar de un error raro más adelante.
**Concepto:** `ImproperlyConfigured` es la excepción que Django usa para errores de configuración.
`python-dotenv` (`load_dotenv`) copia el `.env` a las variables de entorno del proceso.

### T005 · `settings.py` nuevo
**Qué:** todo lo secreto sale de `.env`; PostgreSQL; idiomas; plantillas compartidas en
`templates/`; estáticos en `static/`; correo con `MAILERS`; ajustes de seguridad para producción.
**Concepto:** `MAILERS` es la forma nueva (Django 6.1) de configurar el correo: un diccionario
como `DATABASES`. Si no hay contraseña de aplicación, se usa el backend de consola y los correos
se imprimen en la terminal (ideal para desarrollar).

### T006 · Usuario propio (`cuentas.Usuario`)
**Qué:** un modelo con `email`, `nombres`, `apellidos`, `rol`, `is_active`, `is_staff` y
`fecha_registro`, y su gestor `UsuarioManager`.
**Por qué:** el usuario de Django usa `username`; nosotros queremos entrar con el correo y tener
un rol. Además, `AUTH_USER_MODEL` **solo se puede cambiar antes de la primera migración**; por
eso va en el módulo 001 aunque el registro llegue en el 002.
**Conceptos:**
- `AbstractBaseUser` trae la contraseña cifrada y `last_login`; `PermissionsMixin` trae
  `is_superuser`, grupos y permisos.
- `USERNAME_FIELD = "email"` le dice a Django con qué campo se inicia sesión.
- El correo se guarda en minúsculas (`save()`) y se busca con `email__iexact`
  (`get_by_natural_key`), así `Ana@Correo.com` y `ana@correo.com` son la misma cuenta.
- `models.TextChoices` (`Rol`) define opciones con valor y etiqueta traducible.
- `set_password()` nunca guarda la contraseña en texto plano: guarda un *hash*.

### T007 · Migración inicial
**Qué:** `python manage.py makemigrations cuentas` y `migrate` contra PostgreSQL vacío.
**Concepto:** una migración es un archivo Python que describe cómo cambiar la base de datos.
Nunca se edita ni se borra una migración ya compartida; los cambios van en migraciones nuevas.

### T008 · Usuario en el panel de Django
**Qué:** `UsuarioAdmin` con búsqueda por correo y nombre, filtro por rol y edición del rol.
**Concepto:** `UserAdmin` ya sabe manejar contraseñas; solo se le indican los campos propios
(`fieldsets` y `add_fieldsets`) y formularios adaptados (`AdminUserCreationForm`).

### T010 · Fuentes locales
**Qué:** Unbounded y Archivo en `static/fonts/` (woff2) con sus licencias.
**Por qué:** no depender de Google Fonts (privacidad, funciona sin internet externo).
**Concepto:** `@font-face` declara una fuente; `font-display: swap` muestra el texto de inmediato
con una fuente del sistema mientras carga la nuestra.

### T011 · Tema de Tailwind (`static/src/entrada.css`)
**Qué:** colores institucionales, colores de estado, fuentes, sombras sólidas, animaciones y
componentes (`.btn`, `.tarjeta`, `.insignia`, `.campo-control`, `.aviso`…).
**Conceptos:**
- En Tailwind v4 el tema se define en CSS con `@theme`: `--color-uteq-verde` crea clases como
  `bg-uteq-verde` y `text-uteq-verde`.
- **Tokens semánticos:** variables como `--fondo` o `--texto` cambian dentro de `.dark`, y
  `@theme inline` las convierte en clases (`bg-fondo`, `text-texto`). Por eso casi no hay `dark:`
  en las plantillas.
- `@custom-variant dark (&:where(.dark, .dark *))` hace que `dark:` dependa de una clase en
  `<html>` y no solo del sistema.
- `@media (prefers-reduced-motion: reduce)` apaga las animaciones para quien lo pide.

### T012 · Plantilla base y parciales
**Qué:** `templates/base.html` con encabezado, mensajes, contenido y pie; parciales en
`templates/parciales/`.
**Conceptos:**
- Herencia de plantillas: cada página hace `{% extends "base.html" %}` y llena
  `{% block contenido %}`.
- `{% include %}` reutiliza un trozo y puede recibir variables con `with`.
- El enlace **"Saltar al contenido"** permite a quien navega con teclado saltar el menú.
- El **menú móvil es un `<details>`**: el navegador lo abre y cierra solo, sin JavaScript.

### T013 · Componentes
**Qué:** `boton.html`, `campo.html`, `aviso.html` e `insignia_estado.html`, más el filtro
`{{ campo|control }}` en `vitrina/templatetags/formularios.py`.
**Concepto:** un *template tag* o *filtro* propio es una función Python que se usa en las
plantillas. `control` le pone la clase del tema al campo y conecta sus errores con
`aria-describedby` para que los lectores de pantalla los lean.

### T014 · Logo opcional
**Qué:** `config/contexto.py` busca `static/img/logo-uteq.svg` (o `.png`/`.webp`).
**Concepto:** un *procesador de contexto* agrega variables a todas las plantillas. Para poner el
logo oficial basta con copiar el archivo en `static/img/`; si no existe, se ve el nombre en texto.

### T015 · Portada y páginas "Próximamente"
**Qué:** vista `inicio` con los cuatro pasos y la plantilla `vitrina/inicio.html`; `explorar` y
`verificar` muestran "Próximamente" hasta los módulos 003 y 005.
**Conceptos:** vistas basadas en funciones (`def inicio(request)`), `render()`, y
`app_name = "vitrina"` para usar `{% url 'vitrina:inicio' %}` sin choques de nombres.

### T016 · Inicio de sesión temporal
**Qué:** `templates/registration/login.html` con el diseño nuevo; se borró el registro viejo.
**Por qué:** el registro anterior usaba `UserCreationForm`, que está hecho para el usuario de
Django con `username` y no funciona con el nuestro. El registro real (con activación por correo)
llega en el módulo 002.

### T017 · Compilar Tailwind
**Qué:** `tailwindcss -i static/src/entrada.css -o static/css/app.css --minify`.
**Concepto:** Tailwind lee las plantillas (las rutas `@source`), detecta qué clases se usan y
genera un CSS solo con esas. El resultado se sube al repo para que nadie necesite el ejecutable
para ver la app.

### T019–T021 · Idiomas
**Qué:** `LocaleMiddleware`, `LANGUAGES`, `LOCALE_PATHS`, la ruta `i18n/` y las traducciones
en `locale/en/LC_MESSAGES/django.po` (compiladas en `django.mo`).
**Conceptos:**
- En plantillas: `{% load i18n %}` y `{% translate "Texto" %}`. Con variables:
  `{% blocktranslate with nombre=user.nombres %}Hola, {{ nombre }}{% endblocktranslate %}`.
- En Python: `from django.utils.translation import gettext as _` y `_("Texto")`. En modelos y
  settings se usa `gettext_lazy`, porque se evalúan antes de saber el idioma de la petición.
- El selector hace un POST a la vista `set_language` de Django, que guarda una cookie.
- `config/middleware.py` (`EspanolPorDefectoMiddleware`) ignora el idioma del navegador para
  que un visitante nuevo siempre vea español, como pide la spec.

### T023–T024 · Tema claro y oscuro
**Qué:** un script corto en el `<head>` y `static/js/tema.js`.
**Concepto:** el script del `<head>` corre **antes** de cargar el CSS y de pintar la página, así
que pone la clase `dark` a tiempo y no hay destello. `tema.js` solo maneja el botón, guarda la
elección en `localStorage` y actualiza `aria-label` y `aria-pressed`.

### T025–T026 · Páginas 404 y 500
**Qué:** `templates/404.html` y `templates/500.html`.
**Concepto:** Django las usa solas cuando `DEBUG=False`. La 500 no hereda de `base.html` a
propósito: si el error viene de la base o de una plantilla, esa página igual tiene que mostrarse.

### T027 · Pruebas
**Qué:** 49 pruebas en `cuentas/tests/` y `vitrina/tests/`.
**Conceptos:**
- `SimpleTestCase` no usa base de datos (pruebas de `entorno.py`); `TestCase` crea una base de
  pruebas y la limpia después de cada prueba.
- `self.client` simula un navegador: `get`, `post`, `force_login`.
- `override_settings(DEBUG=False)` prueba las páginas de error; `mock.patch` simula que existe
  el logo o que falta una variable de entorno.

---

## Módulo 002 · Cuentas y autenticación

### T001 · Token de activación (`cuentas/tokens.py`)
**Qué:** un generador que hereda de `PasswordResetTokenGenerator` y agrega `is_active` a los
datos firmados.
**Por qué:** el token de Django ya vence solo (24 h) y está firmado con la `SECRET_KEY`, así que
nadie puede inventarlo. Al sumar `is_active`, en cuanto la cuenta se activa el token cambia y el
enlace deja de servir: es de un solo uso sin guardar nada en la base de datos.
**Concepto:** el enlace lleva `uidb64` (el id del usuario en base64) y el `token`. La vista los
decodifica y llama a `check_token()`.

### T002 · Límite de intentos (`cuentas/limite.py`)
**Qué:** cuenta los fallos por correo e IP en la caché de Django; con 5 fallos bloquea 15 minutos.
**Conceptos:** `cache.add()` crea la clave solo si no existe (con su tiempo de vida) y
`cache.incr()` suma uno. Al vencer el tiempo, la clave desaparece sola. `CACHES` se configura en
`settings.py`; en memoria sirve para un proceso, en producción con varios se usa una compartida.

### T003 · `@rol_requerido` y la página 403
**Qué:** un decorador que redirige a iniciar sesión a quien no tiene sesión y lanza
`PermissionDenied` a quien no tiene el rol.
**Conceptos:** un *decorador* es una función que envuelve a otra (`@wraps` conserva su nombre).
Cuando una vista lanza `PermissionDenied`, Django muestra `templates/403.html` con código 403.

### T004 · URLs con espacio de nombres
**Qué:** `cuentas/urls.py` con `app_name = "cuentas"` y rutas en español; `LOGIN_URL` pasa a
`cuentas:entrar`.
**Concepto:** las vistas de recuperación de Django buscan por defecto nombres sin espacio de
nombres (`password_reset_done`); por eso se les pasa `success_url` con `reverse_lazy("cuentas:…")`.

### T005 · Formulario de registro
**Qué:** `FormularioRegistro` hereda de `BaseUserCreationForm` (que ya valida y confirma la
contraseña con los validadores de `settings.py`).
**Concepto:** los métodos `clean_<campo>()` validan un campo concreto: `clean_email` pasa el
correo a minúsculas y rechaza los repetidos con `email__iexact`.

### T006 · Correos de activación (`cuentas/correos.py`)
**Qué:** `EmailMultiAlternatives` con versión de texto y versión HTML, armadas con plantillas.
**Conceptos:** los correos HTML llevan estilos en línea y tablas porque los programas de correo
ignoran casi todo el CSS. `request.build_absolute_uri()` arma la dirección completa con el dominio.
Si el envío falla, se registra con `logging` y la cuenta no se pierde.

### T007 · Vistas de registro, activación y reenvío
**Qué:** registro → "Revisa tu correo" → enlace → cuenta activa y sesión iniciada.
**Conceptos:** `request.session` guarda datos entre una página y la siguiente (el correo al que
se envió el enlace). `login(request, usuario, backend=...)` inicia la sesión sin pedir la
contraseña (ya la comprobó el enlace). El reenvío responde siempre lo mismo para no revelar
qué correos tienen cuenta.

### T009–T010 · Entrar y salir
**Qué:** `FormularioEntrar` hereda de `AuthenticationForm`; la vista `entrar` aplica el límite de
intentos, la opción "Mantener la sesión iniciada" y una redirección segura.
**Conceptos:**
- `authenticate()` no devuelve usuarios inactivos; para avisar "activa tu cuenta" se comprueba
  aparte que la contraseña sea correcta, y así no se revela nada a quien no la sabe.
- `request.session.set_expiry(0)` hace que la sesión termine al cerrar el navegador.
- `url_has_allowed_host_and_scheme()` impide que `?next=https://otro-sitio` nos use para
  redirigir a páginas falsas (*open redirect*).
- `@require_POST` en `salir`: cerrar sesión cambia el estado, por eso no se acepta por GET.

### T012 · Recuperar la contraseña
**Qué:** las cuatro vistas de Django (`PasswordResetView`, `…DoneView`, `…ConfirmView`,
`…CompleteView`) con nuestras plantillas y correos.
**Concepto:** reutilizar las vistas de Django es más seguro que reescribirlas: ya responden igual
exista o no el correo, solo envían a cuentas activas y quitan el token de la URL antes de mostrar
el formulario.

### T014 · Perfil y cambio de contraseña
**Qué:** `FormularioPerfil` (solo nombres y apellidos) y `CambiarContrasena`, que hereda de
`PasswordChangeView`.
**Concepto:** un `ModelForm` solo guarda los campos de su `Meta.fields`; aunque alguien envíe
`email` o `rol` en el POST, se ignoran. `PasswordChangeView` actualiza la sesión para que no se
cierre al cambiar la contraseña.

### T016 · Pruebas
**Qué:** 44 pruebas nuevas (93 en total), una o más por escenario de aceptación.
**Conceptos:** `mail.outbox` guarda los correos enviados durante la prueba; `override_settings`
cambia un ajuste solo dentro de la prueba (por ejemplo, un plazo vencido); `mock.patch` simula
que el servidor de correo falla; una prueba puede tener sus propias URLs con `ROOT_URLCONF`.

---

## Módulo 003 · Proyectos, Explorar y detalle

### T001 · Modelos con relaciones
**Qué:** `Proyecto` se relaciona con `Asignatura` (muchos a uno), `Tecnologia` (muchos a muchos)
y con los usuarios a través de `Autoria`.
**Conceptos:**
- `ForeignKey(on_delete=PROTECT)`: no se puede borrar una asignatura que ya tiene proyectos.
- `ManyToManyField(through="Autoria")`: cuando la relación necesita datos propios (quién es el
  creador), se usa un modelo intermedio en vez de la tabla automática de Django.
- `TextChoices` para los estados: un solo lugar define el valor guardado y el texto que se muestra.
- Un `QuerySet` propio (`Proyecto.objects.publicados()`) pone la regla "solo aprobados es público"
  en un único sitio, y todas las vistas la reutilizan.

### T002 · Validar archivos de verdad
**Qué:** `validar_pdf` lee los primeros 5 bytes y exige `%PDF-`; las imágenes pasan por Pillow.
**Concepto:** la extensión la elige quien sube el archivo; el contenido no miente. Los archivos se
guardan con un nombre aleatorio (`uuid`), así nadie adivina rutas ni pisa archivos ajenos.

### T003 · Migración de datos
**Qué:** `0002_datos_iniciales` carga las 53 asignaturas de la malla de Ingeniería de Software de la
UTEQ y 42 tecnologías.
**Concepto:** `RunPython` ejecuta código dentro de una migración. Se usa `apps.get_model(...)` y no
el modelo importado, porque la migración debe funcionar con el modelo *tal como era* en ese punto.
Tiene función de reversa para poder deshacerla.

### T005 · Un formulario que guarda varias cosas
**Qué:** `FormularioProyecto` guarda el proyecto, sus tecnologías, autores e imágenes, y la vista lo
llama dentro de `transaction.atomic()`.
**Conceptos:**
- `clean_<campo>()` valida un campo; `clean()` valida combinaciones (máximo 4 imágenes contando
  las que ya hay y las que se quitan).
- `save_m2m()` hace falta cuando se guarda con `commit=False`.
- **Bug que encontraron las pruebas:** el formulario preguntaba "¿quién es el creador?" mirando si
  el proyecto tenía `pk`. Justo después de `save()` ya tiene `pk` pero todavía no tiene autores, y
  el creador salía vacío. La solución fue decidirlo en `__init__`, antes de guardar. Por esto se
  escriben pruebas: el error no se veía al leer el código.

### T006 · Permisos en un solo archivo
**Qué:** `permisos.py` con `puede_ver`, `puede_editar` y `puede_eliminar`.
**Concepto:** las plantillas usan estas funciones para ocultar botones y las vistas para responder
403. Ocultar un botón no protege nada; la comprobación en la vista sí. Un borrador ajeno responde
404 y no 403, para no confirmar que existe.

### T009 · Buscar y filtrar con GET
**Qué:** Explorar usa un formulario `method="get"`, `Q(...) | Q(...)` para buscar en varios campos,
`.distinct()` y `Paginator`.
**Conceptos:** con GET los filtros quedan en la URL y se pueden compartir o guardar. Al buscar a
través de relaciones muchos a muchos un proyecto puede salir repetido; `distinct()` lo evita. La
etiqueta `{% querystring pagina=2 %}` (nueva en Django) cambia un parámetro y conserva los demás.
Los valores raros en la URL (`?pagina=9999`, `?tecnologia=abc`) no rompen la página: el formulario
los descarta y `get_page()` corrige el número.

### T013 · Portada con datos reales
**Qué:** las cifras usan `aggregate`/`count` sobre los proyectos publicados y la portada muestra los
tres más recientes o una invitación si todavía no hay ninguno.
**Concepto:** `select_related` y `prefetch_related` traen las relaciones en pocas consultas en vez de
una por tarjeta (el problema "N+1").

### T015 · Pruebas
**Qué:** 52 pruebas nuevas (145 en total).
**Conceptos:** `SimpleUploadedFile` simula un archivo subido; las imágenes de prueba se crean con
Pillow en memoria; `override_settings(MEDIA_ROOT=...)` manda los archivos a una carpeta temporal que
se borra al terminar, para no ensuciar `media/`.

---

## Módulo 004 · Revisión e historial

### T001 · Un historial que no se puede cambiar
**Qué:** `EventoEstado` guarda cada cambio (estado anterior, nuevo, quién, comentario y fecha).
**Conceptos:**
- `self._state.adding` dice si el objeto se está creando. En `save()` usamos eso para rechazar
  cualquier modificación de un evento ya guardado, y `delete()` lanza un error siempre.
- `on_delete=PROTECT` hacia el proyecto: un proyecto con historial no se puede borrar. Así se
  cumple la regla "un proyecto que salió de Borrador no se elimina" también en la base de datos.
- Límite honesto: `EventoEstado.objects.filter(...).update(...)` se salta `save()`. Por eso el
  admin de Django además lo muestra de solo lectura y nadie usa `update()` sobre el historial.

### T002 · Una sola puerta para cambiar el estado
**Qué:** `proyectos/servicios.py` con la tabla `TRANSICIONES` y la función `cambiar_estado()`.
**Conceptos:**
- **Capa de servicio:** la regla de negocio vive en un solo lugar. Las vistas no saben qué
  transiciones existen; solo llaman al servicio y reaccionan a sus excepciones.
- **La regla como datos:** el diccionario `(desde, hacia) → quién` es la tabla de la
  constitución escrita en Python. Agregar una transición es agregar una línea.
- **`select_for_update()`** dentro de `transaction.atomic()` bloquea la fila del proyecto hasta
  terminar. Si dos profesores pulsan "Tomar" a la vez, el segundo espera, lee el estado real
  (ya En revisión) y recibe `TransicionNoPermitida`. Sin el bloqueo, los dos "ganarían".
- **Código VP con contador:** `Consecutivo` guarda el último número de cada año. Bloquear esa
  fila y sumarle uno es seguro; "buscar el último código y sumar uno" falla con dos
  aprobaciones simultáneas.

### T003 · El admin de Django también obedece
**Qué:** estado, revisor, código y fecha de aprobación son de solo lectura en el admin; el
historial se ve pero no se edita; no se borran proyectos enviados.
**Concepto:** el panel de Django es otra puerta de entrada. Si no se cierra, cualquiera con
acceso al admin podría aprobar sin revisión. `has_change_permission` y `has_delete_permission`
controlan lo que permite cada modelo; la acción masiva "borrar seleccionados" se quita porque
no pregunta proyecto por proyecto.

### T005–T007 · Enviar, bandeja, tomar y decidir
**Qué:** vistas `enviar`, `bandeja`, `tomar` y `revisar`.
**Conceptos:**
- `annotate(fecha=Max("eventos__creado_en", filter=Q(...)))` calcula en la misma consulta la
  fecha de envío de cada proyecto, para ordenar la bandeja por quien más lleva esperando.
- `@require_POST` en `tomar`: cambia datos, así que no se acepta por GET (un enlace o un
  rastreador no puede tomar proyectos sin querer).
- El formulario valida el comentario para mostrar el error junto al campo, y el servicio lo
  vuelve a validar: la regla no depende de que la vista se acuerde.
- `gettext_lazy` para textos definidos al importar el módulo (el diccionario de mensajes): con
  `gettext` normal quedarían traducidos en el idioma de quien cargó el servidor primero.

### T008 · Correo de la decisión
**Qué:** `avisar_decision()` escribe a todos los autores con el resultado y el comentario.
**Conceptos:** se envía después de guardar; si falla, la decisión no se deshace y la vista avisa
al docente. `translation.override("es")` asegura que el correo salga en español aunque el
docente esté usando la página en inglés.

### T010 · Detalle con observaciones e historial
**Qué:** los autores ven la última observación destacada y los botones Editar y Reenviar; autores
y docentes ven la línea de tiempo. El público no ve ni el historial ni los comentarios internos.
**Concepto:** el mismo `include` (`_historial.html`) se reutiliza en el detalle y en la ficha de
revisión: una sola plantilla, un solo lugar para corregir.

### Ajuste del encabezado
Con un botón más ("Bandeja"), el encabezado se partía en dos líneas a 1280 px. Se agrupó la cuenta
en un menú (`<details>`, que funciona sin JavaScript) y `whitespace-nowrap` evita que los textos
se partan. Las capturas en varios anchos sirven justo para detectar esto.

### T011 · Pruebas
**Qué:** 47 pruebas nuevas (192 en total): cada transición permitida y prohibida, cada permiso,
el bloqueo con un objeto desactualizado, el código consecutivo, el historial inmutable, el
correo (y su falla simulada con `mock.patch`) y el admin.
**Concepto:** `client.force_login(usuario)` inicia sesión en una prueba sin pasar por el
formulario; es más rápido cuando lo que se prueba no es el inicio de sesión.

---

## Módulo 005 · QR, certificado y verificación

### T001 · Configuración opcional y fuentes para el PDF
**Qué:** `SITIO_URL` en `.env` (opcional) y las fuentes del sitio en TTF en `static/fonts/pdf/`.
**Conceptos:**
- Una variable opcional lleva un valor por defecto (`variable("SITIO_URL", "")`) y se documenta en
  `.env.example`. Aquí resuelve un problema real de la demo: un QR que apunta a `127.0.0.1` solo
  funciona en el mismo portátil; con la IP de la red, cualquier celular lo abre.
- reportlab no lee woff2 (el formato web). Las fuentes se convirtieron una vez a TTF con
  fontTools, fuera del proyecto, así que no es una dependencia nueva. Unbounded es una fuente
  *variable* (un solo archivo con todos los grosores); se fijó el grosor 800 para el PDF.

### T002 · Generar archivos en memoria
**Qué:** `vitrina/verificacion.py` con `normalizar_codigo`, `url_verificacion`, `qr_png` y
`certificado_pdf`.
**Conceptos:**
- `io.BytesIO` es un "archivo" en memoria: la librería escribe ahí y la vista devuelve esos bytes
  en un `HttpResponse`. No se guarda nada en disco, así que el QR y el PDF nunca quedan
  desactualizados.
- En el `canvas` de reportlab se dibuja con coordenadas en puntos (1/72 de pulgada), y el origen
  (0, 0) está **abajo a la izquierda**, al revés que en la web. `simpleSplit` parte un texto
  largo en líneas que caben en un ancho.
- El QR usa corrección de errores nivel M: se sigue leyendo aunque se dañe parte de la imagen.
- `normalizar_codigo` usa una expresión regular con `fullmatch` para aceptar `vp-2026-0007`,
  `VP20260007` o con espacios, y rechazar todo lo demás antes de consultar la base de datos.

### T003–T004 · Vistas públicas y descargas
**Qué:** `verificar`, `verificar_codigo`, `descargar_qr` y `descargar_certificado`.
**Conceptos:**
- Un formulario GET que, si es válido, **redirige** a la URL del código: así el resultado siempre
  vive en una dirección que se puede compartir.
- Redirección 301 de `vp-2026-0001` a `VP-2026-0001`: una sola dirección "oficial" por código.
- `render(..., status=404)`: la página de "código no válido" se ve bonita pero responde 404, para
  que navegadores y buscadores sepan que no existe.
- `Content-Disposition: attachment; filename=...` hace que el navegador descargue el archivo con
  ese nombre en vez de abrirlo.
- Las descargas filtran con `Proyecto.objects.publicados()`: un proyecto no aprobado no tiene
  QR ni certificado aunque alguien escriba su código a mano.

### T006 · Pruebas y revisión visual
**Qué:** 18 pruebas nuevas (209 en total): formas válidas e inválidas del código, que la página
no muestre correos ni comentarios internos, que el texto raro en la URL salga escapado, que el
PNG y el PDF sean de verdad PNG y PDF (`Pillow` abre la imagen; el PDF empieza por `%PDF-`) y que
`SITIO_URL` cambie la dirección del QR (`override_settings`).
Las capturas a 390 px mostraron que el campo del código desbordaba la pantalla: un `<input>` tiene
un ancho mínimo propio y hay que permitirle encogerse con `min-w-0 w-full`.

---

## Módulo 006 · Paneles por rol

### T001–T003 · Un panel por rol
**Qué:** `/panel/` muestra un resumen distinto al estudiante, al profesor y al admin
(`vitrina/paneles.py`), y es la página a la que se llega después de iniciar sesión.
**Conceptos:**
- **Contar en la base de datos:** `aggregate(aprobados=Count("id", filter=Q(estado="aprobado")), ...)`
  devuelve todas las cifras en **una** consulta. Recorrer los proyectos en Python y contar haría
  una consulta (o más) por proyecto.
- **`Prefetch(..., to_attr=...)`** trae la última observación de varios proyectos en una sola
  consulta extra. La prueba `assertNumQueries(7)` lo comprueba: con 3 o con 4 proyectos para
  corregir, el panel hace exactamente las mismas consultas.
- **Barras sin librerías:** una barra es un `<span>` con `width: X%`. Todas son de un mismo color
  porque miden lo mismo; el número va escrito al lado para que nadie dependa del color o del largo.
- `LOGIN_REDIRECT_URL` decide adónde va la persona al entrar; `resolve_url()` lo convierte en una
  dirección aunque sea un nombre de ruta.

### T004 · Gestión de usuarios y roles
**Qué:** `/cuentas/usuarios/` (lista con búsqueda, filtros y paginación) y la página de gestión de
cada cuenta, solo para admins.
**Conceptos:**
- **Reglas de negocio en el formulario:** `clean()` impide cambiar el propio rol o desactivarse
  (la plataforma nunca se queda sin admin por un clic) y no toca cuentas técnicas de Django.
- `form.has_changed()` y `form.changed_data` dicen qué cambió: si nada cambió, no se registra nada.
- **`LogEntry`** es el registro de acciones que ya trae Django; `log_actions()` guarda quién
  cambió qué. No hizo falta crear un modelo nuevo.
- **Desactivar cierra la sesión:** Django revisa `is_active` en cada petición; una cuenta
  desactivada queda fuera aunque tuviera la sesión abierta (está probado).
- Ser "admin" de la plataforma (`rol`) es distinto de entrar a `/admin/` de Django (`is_staff`):
  uno es de negocio, el otro es técnico.

### T007 · Una migración de datos para arreglar el pasado
**Qué:** `0004_codigos_faltantes` da código a los proyectos que se aprobaron a mano en el 003.
**Conceptos:** las capturas del panel mostraron "None" donde debía ir el código. El arreglo no es
tocar la plantilla, sino los **datos**: una migración `RunPython` que corre una sola vez en cada
base. Su reversa es `noop` porque un código entregado no debe cambiar. Para probar una migración se
usa `MigrationExecutor` (ir a la 0003, crear datos, migrar a la 0004 y revisar), con
`serialized_rollback = True` para que la base quede como estaba para las demás pruebas.

### Ajuste · Las consultas de la bandeja pasan a servicios.py
**Qué:** `consultas_bandeja()` se mudó de `proyectos/views.py` a `proyectos/servicios.py`.
**Por qué:** el panel del profesor (`vitrina/paneles.py`) la necesita, y una app solo puede
importar modelos, formularios o servicios de otra, nunca sus vistas (constitución, principio I).
**Conceptos:** si dos apps necesitan la misma lógica, esa lógica no es de una vista: se lleva a la
capa de servicios y las dos vistas la llaman. Las vistas quedan como "pegamento" entre la petición
y la respuesta.

---

## Módulo 007 · Comunidad

### T001 · Unicidad garantizada por la base de datos
**Qué:** `MeGusta`, `Favorito` y `Comentario` en la app `comunidad`.
**Conceptos:** `UniqueConstraint(fields=["usuario", "proyecto"])` asegura un solo me gusta por
persona aunque pulse dos veces muy rápido: la segunda inserción falla con `IntegrityError` y la
vista simplemente la ignora. Comprobar "¿ya existe?" en Python no basta, porque entre la
comprobación y el guardado puede colarse otra petición (condición de carrera).

### T002 · Un botón que pone y quita
**Qué:** `me_gusta` y `favorito` son "interruptores": la misma URL agrega o quita.
**Conceptos:** `delete()` devuelve cuántas filas borró; si borró alguna, era quitar; si no, se
crea. `transaction.atomic()` alrededor del `create` aísla el posible `IntegrityError` para que
no rompa el resto de la petición.

### T003 · Comentarios y moderación
**Qué:** comentar, borrar el propio comentario y ocultar (autores del proyecto y admins).
**Conceptos:**
- **Ocultar en vez de borrar:** el moderador puede equivocarse; con `oculto`, `ocultado_por` y
  `ocultado_en` la decisión es reversible y queda constancia.
- **Límite de envíos con la caché:** `cache.add()` crea el contador solo si no existe (con su
  vencimiento de 10 minutos) y `cache.incr()` lo sube. Es el mismo patrón del límite de intentos
  de inicio de sesión del módulo 002.
- **Escapado:** `{{ com.texto|linebreaksbr }}` escapa el HTML antes de convertir los saltos de
  línea; un `<script>` en un comentario se ve como texto (está probado).
- Los botones son formularios POST que redirigen a la ficha con un ancla (`#comentario-12`):
  todo funciona sin JavaScript.

### T004 · Contar sin duplicar
**Qué:** las tarjetas muestran los me gusta y Explorar ordena por "Más gustados".
**Concepto:** al filtrar por tecnología o autor, la consulta une otras tablas y cada proyecto
puede aparecer varias veces antes del `distinct()`. `Count("me_gustas", distinct=True)` cuenta
personas distintas, no filas repetidas. Hay una prueba que busca por tecnología justo para
comprobar que el conteo no se infla.

---

## Correcciones

### Menú · "Cómo funciona" se marcaba como "Inicio"
**Qué:** en la portada, el menú marca "Cómo funciona" mientras esa sección está a la vista.
**Por qué:** "Cómo funciona" no es otra página sino un ancla (`/#como-funciona`). El navegador
nunca envía la parte `#...` al servidor, así que Django solo sabe que estás en la portada y marca
"Inicio". Lo que pasa dentro de una misma página solo lo puede saber el navegador.
**Conceptos:**
- **`IntersectionObserver`** avisa cuando un elemento entra o sale de la pantalla, sin escuchar
  cada movimiento del scroll. Con `rootMargin: "-50% 0px -50% 0px"` la zona observada es solo la
  línea central de la pantalla.
- **Atributos `data-*`:** la plantilla deja en cada enlace su clase activa (`data-clase-activa`),
  así el JavaScript no repite clases de Tailwind y sirve igual para el menú de escritorio y el móvil.
- `aria-current="location"` le dice al lector de pantalla que esa es la sección actual dentro de
  la página (`"page"` es para la página completa).
- **Mejora progresiva:** sin JavaScript todo sigue funcionando; solo se pierde el resaltado.

### Cuentas · una cuenta desactivada se podía reactivar sola
**Qué:** si un admin desactivaba una cuenta, la persona podía pedir "reenviar activación", abrir
el enlace y quedar activa otra vez. Ahora el enlace solo sirve para cuentas que nunca se activaron,
y al intentar entrar una cuenta desactivada ve un mensaje propio en vez de "abre el enlace".
**Por qué:** "sin activar" y "desactivada" se guardaban igual (`is_active=False`). Lo que las
distingue es `last_login`: activar la cuenta inicia sesión, así que una cuenta que ya se usó
siempre tiene fecha de último ingreso. Es el mismo criterio que ya usaba el filtro de usuarios.
**Concepto:** cuando un campo booleano mezcla dos situaciones distintas, hay que buscar otro dato
que las separe (o agregar un campo). Las pruebas `cuentas/tests/test_desactivadas.py` lo cubren.

### Revisión · el certificado nombraba a quien tomó el proyecto, no a quien lo aprobó
**Qué:** si un profesor tomaba un proyecto y luego decidía un admin, el certificado y la página de
verificación decían "aprobado por" el profesor. Ahora `cambiar_estado()` deja como revisor a quien
toma el proyecto y, al decidir, a quien decide.
**Concepto:** un dato público que "certifica" algo debe salir del hecho que certifica (la
decisión), no de un paso anterior (tomar el proyecto). El historial completo sigue en `EventoEstado`.

### Proyectos · solo el creador cambia la lista de coautores
**Qué:** un coautor podía, al editar, quitar a otros coautores o quitarse a sí mismo. Ahora el
campo aparece bloqueado para quien no es el creador; el resto del proyecto lo sigue editando.
**Concepto:** `field.disabled = True` en un formulario de Django no solo desactiva el control en
el HTML: Django ignora lo que llegue en el POST para ese campo y usa el valor inicial, así que
tampoco sirve modificar la petición a mano.

### Proyectos · un coautor puede salir del proyecto
**Qué:** en Mis proyectos, un coautor tiene el enlace "Salir". Pide confirmación, lo quita del
proyecto y le avisa por correo al creador. El creador sigue quitando a cualquiera desde el campo
Coautores al editar.
**Reglas y por qué:**
- Solo mientras el proyecto se puede editar (Borrador o Con observaciones). Después de enviado,
  la lista de autores es parte de lo que el docente revisa y de lo que el certificado garantiza;
  si cambiara, un certificado ya entregado mostraría otros nombres en la página de verificación.
- El creador no puede salir: el proyecto se quedaría sin dueño. Si ya no lo quiere, lo elimina.
- Es un botón aparte con su propia confirmación, no borrar tu correo del campo Coautores: una
  acción que te deja sin acceso no debe pasar por accidente al editar otra cosa.
- El correo al creador se envía después de guardar; si falla, la salida igual queda hecha.
**Concepto:** las reglas de "quién puede" viven en `proyectos/permisos.py` (`puede_salir`) y las
usan tanto la vista (403) como la plantilla (mostrar el enlace).

### Proyectos · transferir el proyecto a un coautor
**Qué:** en Mis proyectos, el creador tiene el enlace "Transferir". Elige a un coautor, ese pasa
a ser el creador y el anterior queda como coautor (si quiere irse, después usa "Salir"). Se le
avisa por correo al nuevo creador.
**Reglas:** solo el creador, solo en Borrador o Con observaciones (las mismas reglas que "Salir")
y solo a coautores con cuenta activa. Siempre hay exactamente un creador.
**Conceptos:**
- El dueño no es un campo de Proyecto sino `Autoria.es_creador`. Transferir es cambiar dos filas:
  quitar la marca a una y ponérsela a otra. Por eso van dentro de `transaction.atomic()`: o
  cambian las dos o ninguna, y nunca queda un proyecto con cero o dos creadores.
- `select_for_update()` bloquea esas filas mientras dura la transacción. Si el creador manda el
  formulario dos veces seguidas, la segunda petición espera y luego ve que ya no es el creador.
- `ModelChoiceField` solo acepta valores de su `queryset`: si alguien manda en el POST el id de
  una persona que no es coautora, el formulario lo rechaza sin que escribamos esa validación.

---

## Spec 008 · Ajustes pedidos por el profesor

### Historia 1 · Una persona puede tener varios roles y elige con cuál entrar
**Qué:** antes `Usuario.rol` era un solo campo. Ahora cada rol que tiene una persona es una fila de
`RolAsignado` (estudiante, profesor, admin) y en la sesión se guarda con cuál está actuando: el
**rol activo**. Quien tiene más de uno ve "Entrar como" en el menú de su cuenta; el rol activo
siempre se ve en el encabezado. En el perfil, "Mis roles" dice desde cuándo tiene cada uno.
**Reglas y por qué:**
- Lo que ves y puedes hacer depende del rol activo, no de todos tus roles juntos. Así una
  profesora que también es estudiante no mezcla sus proyectos con la bandeja de revisión, y un
  admin sabe cuándo está actuando con más permisos.
- Toda cuenta conserva al menos un rol y nunca se le quita el rol admin al último admin activo:
  si no, la plataforma podría quedarse sin nadie que gestione usuarios.
- Conflicto de interés: quien actúa como profesor o admin no revisa un proyecto del que es autor.
  Su proyecto no aparece en su bandeja y, si llega a la ficha de revisión, ve el motivo.
- Cada rol dado o quitado queda en `CambioRol` con quién lo hizo y cuándo.
**Conceptos de Django:**
- **Relación uno a muchos en vez de un campo con opciones.** `RolAsignado` tiene una
  `ForeignKey` al usuario y `UniqueConstraint(usuario, rol)`: la base de datos garantiza que nadie
  tenga el mismo rol dos veces.
- **Middleware** (`config/middleware.py`): código que corre en cada petición antes de la vista.
  `RolActivoMiddleware` lee el rol de la sesión, comprueba que la persona todavía lo tenga y lo
  deja en `request.user.rol_activo`. La sesión nunca se cree a ciegas: si alguien la manipula o
  un admin le quitó ese rol, se usa su rol por defecto.
- **Procesador de contexto** (`config/contexto.py:roles`): entrega `rol_activo` y
  `roles_disponibles` a todas las plantillas sin pasarlos en cada vista.
- **Migración de datos en tres pasos** (cuentas 0002–0004): 1) crear las tablas nuevas, 2)
  `RunPython` copia el rol de cada usuario a `RolAsignado`, 3) borrar el campo viejo. Cada paso
  tiene su vuelta atrás: al revertir, `Usuario.rol` recibe el rol de mayor privilegio.
- **`prefetch_related("roles_asignados")`** en la lista de usuarios: las etiquetas de rol de 20
  personas llegan en una sola consulta extra, no en 20.
- Un **servicio único** (`cuentas/roles.py`), como `cambiar_estado`: las reglas viven en un solo
  lugar y se cumplen se cambie el rol desde la web, el admin de Django o una prueba.

### Historia 2 · El admin administra los periodos académicos
**Qué:** el periodo dejó de ser un texto "AAAA-1/AAAA-2" y ahora es el modelo `Periodo` (nombre
libre, tipo, fechas y si está abierto para entregas). El admin lo gestiona en Mi panel →
Periodos académicos. Al crear un proyecto solo se eligen periodos abiertos; Explorar filtra con
un slug legible (`?periodo=intensivo-noviembre-2026`).
**Reglas y por qué:**
- Un periodo con proyectos no se borra (`on_delete=PROTECT`): se cierra. Borrarlo dejaría
  proyectos aprobados, con certificado, sin periodo.
- Si editas un proyecto cuyo periodo ya cerró, lo conservas como opción: cerrar un periodo no
  debe obligar a cambiar proyectos viejos.
**Conceptos de Django:**
- **Pasar de `CharField` a `ForeignKey` sin perder datos** (proyectos 0005–0007): campo nuevo
  nulo → `RunPython` crea un `Periodo` por cada texto distinto y lo asigna → quitar el texto y
  renombrar. Antes de quitarlo se le pone un valor por defecto: así, al revertir, Django puede
  volver a crear la columna en una tabla que ya tiene filas.
- **`ModelChoiceField(to_field_name="slug")`**: el formulario de filtros recibe el slug en la URL
  y devuelve el objeto `Periodo`.
- **Unir querysets con `|`**: periodos abiertos `|` el periodo actual del proyecto.
- Una migración vieja importa `validar_periodo` y las migraciones existentes no se tocan: la
  función se conserva, documentada, solo para esa migración.

### Historia 3 · El admin configura desde la app el correo que envía los mensajes
**Qué:** página "Correo de envío" (solo admin): servidor, puerto, seguridad, usuario,
contraseña de aplicación y remitente, con configuración rápida para Gmail y Outlook, botón
"Probar configuración" y una tarjeta de estado. Sin configuración guardada, todo funciona como
antes (`.env` o consola).
**Reglas y por qué:**
- La contraseña se guarda **cifrada** y nunca se vuelve a mostrar; dejar el campo vacío la
  conserva. Quien vea la base de datos (o una copia de seguridad) no puede leerla sin `CLAVE_CIFRADO`.
- "Probar" usa lo escrito sin guardarlo y tiene límite de intentos (`cuentas/limite.py`): así no
  se puede usar la página para probar contraseñas a lo bruto.
- Los errores se traducen a mensajes claros (credenciales rechazadas, servidor que no responde,
  problema TLS/SSL) y nunca muestran el detalle técnico.
**Conceptos:**
- **Cifrado simétrico con Fernet** (`cryptography`): la misma clave cifra y descifra, y detecta
  si el texto fue alterado. La clave vive en el `.env`, no en la base.
- **`MAILERS` de Django 6.1**: cada entrada dice qué clase envía (`BACKEND`) y con qué opciones.
  Escribimos un backend propio (`config/correo.py`) que en cada envío elige entre la configuración
  de la app y el respaldo del `.env`, y delega en el backend SMTP de Django.
- **Caché con invalidación**: la configuración se lee de la caché; `ConfiguracionCorreo.save()`
  borra la clave para que el siguiente correo use los datos nuevos.
- **Singleton**: `save()` fija `pk = 1`, así siempre hay una sola fila de configuración.
- **Pruebas sin servidor real**: `override_settings(MAILERS=...)` con el backend en memoria y
  `mock.patch` sobre `send_messages` para simular respuestas y errores SMTP.

### Historia 4 · Comentarios: etiqueta de autor y respuestas del autor
**Qué:** el comentario de un autor del proyecto lleva la etiqueta amarilla "Autor" y se destaca
con un borde verde grueso. Los autores responden comentarios (un solo nivel, con sangría). Si
quien comenta es el docente que revisó el proyecto, lleva "Docente revisor". Cuando un autor
responde, se avisa por correo a quien comentó.
**Reglas y por qué:**
- Solo los autores responden: la conversación es entre el público y quienes hicieron el proyecto.
- No se responde a una respuesta: con un nivel la página se lee fácil en el celular.
- Ocultar un comentario oculta su hilo: las respuestas sin la pregunta no tienen sentido.
- La etiqueta lleva texto, no solo color, para quien no distingue colores.
**Conceptos de Django:**
- **`ForeignKey("self")`**: un comentario apunta a otro comentario de la misma tabla.
- **Validación en el modelo** con `clean()` y `full_clean()`: la regla de un solo nivel vale
  aunque alguien arme el POST a mano.
- **`Prefetch("respuestas", queryset=..., to_attr="hilo")`**: las respuestas de todos los
  comentarios llegan en una sola consulta, ya filtradas y ordenadas. Los ids de los autores se
  calculan una vez. Una prueba comprueba que más comentarios no significan más consultas (sin N+1).

### Historia 5 · Identidad visual completa
**Qué:** favicon, ícono de iPhone, manifest y vista previa al compartir en todas las páginas;
logo verde en modo claro y blanco en modo oscuro; sellos de la Facultad y de la Carrera en el
pie, en entrar/registro/recuperar y en la verificación; logo y sellos en el certificado PDF; logo
en los correos HTML y en la página 500. Al compartir un proyecto aprobado por WhatsApp sale su
título, su resumen y su portada.
**Conceptos:**
- **`<picture>`** con `<source type="image/webp">` y un `<img>` PNG de respaldo: el navegador
  elige el formato más liviano que entienda.
- **`width` y `height` en las imágenes**: el navegador reserva el espacio antes de descargarlas
  y la página no "salta" al cargar.
- **Open Graph** (`og:title`, `og:image`…): metadatos que leen WhatsApp, LinkedIn o Facebook para
  armar la tarjeta. La imagen necesita una URL absoluta (`request.build_absolute_uri`).
- **Correos**: los programas de correo no entienden rutas relativas, por eso el logo usa
  `SITIO_URL` o la dirección de la petición. En la recuperación de contraseña, Django ya entrega
  `protocol` y `domain` a la plantilla.
- **La página 500 no usa procesadores de contexto** (puede que el error venga de ellos): el logo
  se pide con `{% static %}` directo.
- **reportlab no lee webp ni SVG**: el certificado usa las versiones PNG grandes de `static/img/marca/`.

## Spec 009 · Perfiles, profesor revisor elegido, período actual y navegación

**Línea base (25-nov-2026):** antes de empezar, `python manage.py test` → 357 pruebas, todas en verde.
Todo lo que pasaba antes tiene que seguir pasando al final.

**Enmienda de la constitución (3.0.0):** la 009 cambia reglas que la constitución fijaba, así que
primero se enmienda y después se programa. Es MAJOR porque cambia reglas existentes: el revisor
lo elige el creador del proyecto y lo acepta el profesor; solo el profesor asignado decide (el
admin reasigna); la foto de perfil y la portada admiten hasta 5 MB.

### Base · Íconos SVG, imágenes subidas y pruebas más rápidas
**Qué:** los íconos (Tabler Icons y los logos de GitHub, LinkedIn y ORCID) quedan guardados en
`static/iconos/` y se insertan con `{% icono "nombre" %}`. `config/imagenes.py` valida y convierte
las imágenes que suben las personas. Las pruebas usan un ejecutor propio (`config/pruebas.py`).
**Conceptos de Django:**
- **Etiqueta de plantilla propia** (`@register.simple_tag`) y **filtro** (`@register.filter`).
  Con `"builtins"` en `TEMPLATES` quedan disponibles en todas las plantillas sin `{% load %}`.
- **`mark_safe` con cuidado**: solo sobre archivos del repositorio; lo que viene del usuario
  (la etiqueta accesible) se escapa con `escape()`.
- **`lru_cache`**: cada SVG se lee del disco una vez por proceso.
- **Pillow para validar**: la extensión no prueba nada; `Image.open().verify()` sí. Volver a dibujar
  la imagen en webp borra los metadatos (GPS) y cualquier cosa escondida en el archivo.
- **`TEST_RUNNER`**: el ejecutor vacía la caché antes de cada prueba (el rollback no la deshace) y
  usa un hasher de contraseñas rápido solo en pruebas: la suite pasó de 7 minutos a menos de uno.

### Historia 1 · Un solo período actual
**Qué:** el admin marca un período como "actual" (con confirmación). El estudiante ya no elige
período: al enviar el proyecto toma el actual; si no hay, no puede enviar. Al aprobar se guarda
también el período de aprobación, que muestran la verificación y el certificado. El pie dice
"Período académico actual: …" a todo el mundo.
**Reglas y por qué:**
- Un solo actual, garantizado por la base de datos, no solo por el código: dos admins que marcan a
  la vez no pueden dejar dos actuales.
- Primero se desmarca el anterior y luego se marca el nuevo, en una transacción: al revés, por un
  instante habría dos y la restricción lo rechazaría.
- El período se asigna en `servicios.cambiar_estado`, la única puerta de los estados: así no hay
  forma de enviar sin período, venga de la vista que venga.
**Conceptos de Django:**
- **`UniqueConstraint(fields=["es_actual"], condition=Q(es_actual=True))`**: restricción única
  *parcial*. Solo cuentan las filas con `True`; las `False` pueden repetirse.
- **Migración en tres pasos** (campo nuevo → datos con `RunPython` → quitar el campo viejo), cada
  uno reversible. Una prueba migra hacia atrás y hacia adelante con `MigrationExecutor`.
- **Caché con invalidación**: `Periodo.actual()` guarda el resultado y `save()`/`delete()` lo
  borran. Se guarda un valor especial para "no hay período", porque `None` en la caché significa
  "no está guardado".
- **Procesador de contexto** (`config.contexto.periodo_actual`): el pie lo recibe en todas las páginas.
- **`ForeignKey(..., null=True, on_delete=PROTECT)`**: el borrador no tiene período, y un período
  con proyectos no se puede borrar.

### Historia 2 · Arreglos rápidos: correo, tildes y "Guardados"
**Qué:**
- *Correo de envío*: las instrucciones cambian según el botón (Gmail, Outlook / Microsoft 365 o
  Personalizado), con enlaces directos a la página de contraseñas de aplicación de cada proveedor.
  Si Microsoft responde con 5.7.139 o 5.7.30 se explica que bloqueó el inicio con contraseña.
- *Tildes*: el texto que escriben las personas se guarda en NFC; la portada de color toma la
  primera letra completa (filtro `|inicial`) y el certificado cambia los caracteres que su fuente
  no trae (por ejemplo `→` por `->`) en vez de dibujar una caja con una x.
- *Guardados*: "Favoritos" pasa a llamarse "Guardados" en todas partes; `/comunidad/favoritos/`
  redirige a `/comunidad/guardados/`.
**Por qué salía la "cajita":** en el navegador nunca sale, porque si a una fuente le falta un
carácter el navegador busca otra. reportlab no: dibuja el glifo vacío de la fuente. Además, un
texto copiado de macOS o de un PDF puede venir en NFD («n» + tilde suelta), que reportlab no compone.
**Conceptos de Django y Python:**
- **Mejora progresiva**: las tres ayudas se dibujan en el servidor; el JavaScript solo esconde las
  que no tocan. Sin JavaScript se ven todas, con su título.
- **`unicodedata.normalize("NFC", …)`** en una mezcla de formulario (`FormularioNFC`) que toca
  `cleaned_data` en `clean()`: un `ModelForm` copia esos datos al modelo después.
- **`RenameModel`** en una migración: cambia el nombre del modelo y de su tabla sin tocar las
  filas. Una prueba migra hacia adelante y hacia atrás y comprueba que nadie pierde lo guardado.
- **`RedirectView.as_view(pattern_name=..., permanent=True)`**: una dirección vieja que responde 301.
- **`smtplib.SMTPResponseException.smtp_error`**: el texto que devolvió el servidor, donde vienen
  los códigos ampliados como 5.7.139.

### Historia 3 · Plan de estudios y asignaturas administrables
**Qué:** en "Mi panel → Plan de estudios" el admin crea, edita, activa y desactiva planes ("Plan
2026") y, dentro de cada uno, sus asignaturas (nombre, código, semestre). En el formulario del
proyecto las asignaturas salen agrupadas por plan y semestre, con un buscador.
**Qué se fusionó al migrar:** nada. Las asignaturas ya eran una lista (modelo `Asignatura`) desde
el módulo 003, no texto libre; las 53 pasaron al plan "Plan vigente". Igual la migración fusiona las
que solo se diferencian en mayúsculas o espacios, por si alguna base las tuviera, y lo imprime.
**Reglas y por qué:**
- Puede haber varios planes activos: mientras la carrera cambia de plan conviven los dos.
- El nombre se repite entre planes pero no dentro del mismo plan.
- Lo que está en uso no se borra, se desactiva: borrar dejaría proyectos sin asignatura. Quien ya
  tiene una asignatura desactivada la conserva y la sigue viendo en su formulario.
**Conceptos de Django:**
- **`UniqueConstraint(fields=["plan", "nombre"])`**: unicidad compuesta, garantizada por la base.
- **`on_delete=PROTECT`**: la base de datos impide borrar un plan con asignaturas.
- **QuerySet propio** (`Asignatura.objects.ofrecidas()`): la regla "activa y de plan activo" se
  escribe una vez y se reutiliza.
- **`<optgroup>`**: en Django, un `choices` con tuplas `(grupo, [(valor, texto), ...])` dibuja
  grupos dentro del `<select>`.
- **Migración en tres pasos** con `RunPython` (crear plan y campo nulo → datos → campo
  obligatorio y restricción).

### Historia 4 · Perfil público de cada usuario
**Qué:** cada estudiante y profesor tiene un perfil público en `/personas/<slug>/` (lo ven también
los visitantes): foto o iniciales, descripción, aptitudes, experiencia, estudios, GitHub, LinkedIn,
ORCID, asignaturas que imparte (profesores), proyectos publicados y personas relacionadas. Cada
bloque sale solo si tiene contenido y el correo nunca se muestra. El dueño lo edita en la misma
página. En el primer inicio de sesión aparece "Completa tu perfil". Los nombres de autores, revisor
y comentaristas enlazan a su perfil. Explorar busca también por autor y muestra un bloque "Personas".
**Reglas y por qué:**
- Quien solo es admin no tiene perfil visible: el admin no publica ni revisa proyectos.
- El slug sale del nombre y no cambia nunca: un enlace compartido sigue funcionando aunque la
  persona corrija su nombre. Nunca se usa el correo ni el id (no se adivinan otros perfiles).
- Personas relacionadas solo de proyectos aprobados: lo demás todavía no es público.
- ORCID se valida con su dígito de control (norma ISO 7064 11,2): un número mal copiado se detecta.
**Conceptos de Django:**
- **`OneToOneField`** (`Perfil.usuario`): un perfil por persona; se lee como `usuario.perfil`.
- **Señal `post_save`** (`cuentas/signals.py`, conectada en `AppConfig.ready()`): toda cuenta nueva
  recibe su perfil, se cree desde donde se cree. Las que ya existían lo reciben en una migración de datos.
- **`UniqueConstraint(Lower("nombre"))`**: unicidad sin distinguir mayúsculas, en la base de datos.
- **Formularios con `prefix`**: varios formularios en una página sin que sus campos choquen.
  Cada uno manda `seccion` y la vista sabe cuál procesar; con errores se vuelve a dibujar la página
  con lo escrito, y si todo va bien se redirige (patrón POST/Redirect/GET).
- **`Concat("nombres", Value(" "), "apellidos")`**: buscar por nombre completo en la base de datos.
- **Pocas consultas para "personas relacionadas"**: tres consultas traen solo parejas
  `(persona, proyecto)` con `values_list` y una cuarta trae los perfiles; se juntan en Python. Una
  prueba comprueba que más proyectos no significan más consultas.
- **`select_related("usuario__perfil")` + `prefetch_related("usuario__roles_asignados")`**: el
  enlace a cada perfil sale sin una consulta por persona.

### Historia 5 · El estudiante elige al profesor que revisa su proyecto
**Qué:** al enviar, el creador elige al profesor revisor: hasta 5 sugerencias con su motivo ("Imparte
Bases de datos", "Ha revisado 4 proyectos de esta asignatura") y la lista completa con búsqueda,
filtros y orden. El profesor recibe un correo y la solicitud en "Solicitudes de revisión": acepta
(pasa a En revisión a su nombre) o no acepta (con mensaje y recomendación opcionales). Si no
responde en 5 días, el creador la retira. El admin reasigna. Al reenviar con observaciones el
proyecto vuelve al mismo profesor. Solo el profesor asignado decide. Todo queda en el historial.
**Decisión: subestados, no estados nuevos.** "Por asignar revisor", "Esperando aceptación" y "Por
revisar" son momentos del estado Enviado. Se deducen de dos datos que ya existen (el revisor del
proyecto y si hay una solicitud pendiente), así que `Proyecto.subestado` es una propiedad, no un
campo. Ventajas: los seis estados de la constitución no cambian, ni los filtros, insignias, paneles
o pruebas que ya los usaban; y no hay dos lugares donde guardar lo mismo (que podrían contradecirse).
La única regla que cambia en la tabla `TRANSICIONES` es quién pasa de Enviado a En revisión: el
profesor asignado (al aceptar, o al retomar un reenvío).
**Otras reglas y por qué:**
- Una sola solicitud pendiente por proyecto, garantizada por la base de datos (restricción única
  condicional, como el período actual).
- Las pendientes de cada profesor solo informan: nunca impiden elegirlo.
- Quien ya no aceptó no sale en las sugerencias (no insistir), pero se puede volver a elegir.
- El historial guarda también las acciones de las solicitudes con un campo `accion`: así la
  línea de tiempo cuenta toda la historia y sigue siendo una sola e inmutable.
**Conceptos de Django:**
- **`Subquery` + `OuterRef` con `Coalesce`**: contar pendientes y revisados de cada profesor sin
  que los `JOIN` multipliquen filas (un `Count` con varios `JOIN` contaría de más).
- **`Exists`** en `con_subestado()`: anotar si hay una solicitud pendiente sin traerla.
- **`select_for_update()` dentro de `transaction.atomic()`**: si dos personas responden la misma
  solicitud a la vez, la segunda ve que ya no está pendiente.
- **Comando de gestión** (`python manage.py recordar_solicitudes`): el recordatorio del tercer día,
  para programarlo una vez al día.
- **`<dialog>` y `<template>`**: el resumen del perfil del profesor se abre sin salir de la página
  ni perder la elección; sin JavaScript, el nombre abre el perfil en otra pestaña.
- **El atributo `form=`** de HTML: los filtros (GET) viven dentro del formulario de la elección
  (POST) sin anidar formularios, que no está permitido.

### Historia 6 · Menú de la cuenta con íconos y opciones rápidas
**Qué:** la barra superior queda mínima: logo, "Explorar", buscador y el avatar (o, sin sesión,
"Entrar", "Registrarse" y un engranaje con tema e idioma). El menú del avatar muestra nombre, rol
activo y período actual; cambia de rol con un clic; trae "Mi perfil", "Panel", las opciones rápidas
del rol activo (con contadores para el profesor), tema, idioma y "Cerrar sesión". Todos los botones
de acción llevan ícono.
**Reglas y por qué:**
- Mejora progresiva: sin JavaScript el avatar es un enlace a "Mi cuenta", una página con las mismas
  opciones (el mismo parcial `menu_cuenta.html`), y el engranaje es un `<details>`.
- Accesible con teclado: `aria-haspopup` y `aria-expanded`; al abrir, el foco va al primer ítem; las
  flechas recorren el menú; `Esc` cierra y devuelve el foco al avatar.
- En celular el menú se abre como hoja de ancho completo (clases `fixed inset-x-0` que en pantallas
  grandes pasan a `sm:absolute sm:w-80`).
**Conceptos de Django:**
- **Procesador de contexto con consultas condicionales** (`config.contexto.menu_cuenta`): los
  contadores solo se calculan si el rol activo es profesor, y es una consulta por contador. Una
  prueba comprueba que más solicitudes no significan más consultas.
- **Parcial reutilizado** en dos lugares (menú y página): una sola fuente para las opciones.
- **Un componente con parámetros** (`componentes/boton.html` ahora acepta `icono`).

### Historia 7 · Detalles del proyecto: portada, color, demo y video
**Qué:** el estudiante puede subir una imagen de portada (se recorta a 16:9, 1200 × 675, en webp),
que es la cara del proyecto en la vitrina, en el detalle y al compartirlo; puede quitarla y volver a
la portada de color. Sin imagen, elige un color de una paleta de 10, con vista previa en vivo. En el
detalle, "Ver proyecto desplegado" y "Ver video" aparecen junto al repositorio si están llenos.
**Reglas y por qué:**
- Se guarda la clave del color ("vino"), no el código: si se ajusta un tono, cambia en todos.
- Todos los colores tienen contraste ≥ 4.5:1 con el texto blanco de la portada (lo comprueba una
  prueba con la fórmula de las pautas WCAG), así se lee en modo claro y oscuro.
- Los enlaces solo aceptan `http`/`https` (nada de `javascript:`), se abren en pestaña nueva con
  `rel="noopener noreferrer"` (la página abierta no puede tocar la nuestra) y el video solo se
  enlaza, no se incrusta.
- Para que ningún proyecto cambiara de cara, una migración de datos convirtió la primera captura de
  la galería en su portada.
**Conceptos de Django:**
- **`choices`** en un `CharField`: la base de datos guarda la clave y el formulario valida que sea
  una de la paleta.
- **`ImageField` + conversión propia**: el formulario recibe el archivo, `config/imagenes.py` lo
  valida y lo convierte, y `FieldFile.save(nombre, contenido)` lo guarda con nombre aleatorio. El
  archivo anterior se borra a mano (borrar o reemplazar el valor del campo no borra el archivo).
- **Migración de datos con archivos**: `RunPython` abre la imagen con Pillow desde el almacenamiento
  de Django y guarda la nueva; si un archivo falta, ese proyecto se salta en vez de fallar.

## Correcciones del 26 de noviembre

### El menú "roto", el modo oscuro que borraba textos y las fotos estiradas
**Qué pasaba:** el código estaba bien; el navegador seguía usando un `app.css` viejo guardado en su
caché. A ese CSS le faltaban justo las clases nuevas de la spec 009 (`sm:absolute`, `dark:inline`,
`w-12`…), así que el menú caía dentro del encabezado, "Modo claro" quedaba oculto y las fotos
tomaban su ancho real (400 px).
**Arreglo:** la etiqueta `{% estatico 'css/app.css' %}` (en `vitrina/templatetags/iconos.py`) agrega
`?v=<huella del archivo>` a la dirección. Si el archivo cambia, cambia la dirección y el navegador lo
descarga de nuevo. Se usa para el CSS y todos los JS.
**Concepto:** *cache busting*. En producción Django ofrece `ManifestStaticFilesStorage`, que hace lo
mismo al correr `collectstatic`.

### Portada de color con el título
Sin imagen, la portada es HTML (`templates/parciales/portada_color.html`): el color elegido, un
marco blanco, el título completo, una barra amarilla y "Vitrina de Proyectos · UTEQ". Por ser texto
y no una imagen generada, las tildes, la ñ, la diéresis y «» ¿? se ven siempre. Las medidas usan
`cqw` (porcentaje del ancho del contenedor, con `@container` de Tailwind), así se ve igual en una
tarjeta, en el detalle y en la vista previa del formulario.

### Logo en los correos
El `<img>` apuntaba a `http://127.0.0.1:8000/static/...`; Gmail descarga las imágenes desde sus
servidores y no puede entrar a tu computador. Ahora el logo va **dentro** del correo
(`multipart/related` con `Content-ID: <logo-uteq>`, ver `config/correo.py → CorreoConLogo`) y la
plantilla lo pide con `src="cid:logo-uteq"`. Se ve en local y en producción.

### Otros arreglos
- "Mis roles" ya no repite la fecha de "Miembro desde": solo el rol y si está activo.
- Tablas con desplazamiento horizontal (usuarios, períodos, plan, mis proyectos): el contenedor con
  `overflow-x-auto` ahora es `relative`. Sin eso, los textos `sr-only` (que son `position:absolute`)
  se salían del contenedor y la página entera se movía de lado en el celular.
- Rejillas de tarjetas: `grid-cols-1` en celular. Una rejilla sin columnas definidas mide su única
  columna por el contenido más largo (un texto con `truncate`) y las tarjetas se salían de la pantalla.
- Pie de página: con sesión iniciada muestra Panel, Mi perfil y Datos de la cuenta en vez de
  "Iniciar sesión" y "Crear cuenta".
- Perfil en modo edición: el ícono de "Editar descripción" y "Editar GitHub…" ya no queda en una
  línea aparte.

## Spec 010 · Configuración inicial: crear el primer admin desde la app

### Historia 1 · Código de un solo uso y logs por consola
**Qué se hizo:** en un servidor nuevo (base vacía) ya no hace falta `createsuperuser`. El comando
`python manage.py codigo_configuracion_inicial` imprime un código de 12 caracteres que sirve 30
minutos y una sola vez para crear el primer admin en `/configuracion-inicial/`. Si alguien abre esa
página sin un código vigente, el servidor genera uno y lo escribe en el log (respaldo). Todo vive en
`cuentas/configuracion_inicial.py`, y el estado en el modelo `ConfiguracionInicial` (una sola fila).
**Por qué un código:** si la app queda publicada sin admin, cualquiera que vea la página podría
adueñarse de ella. Con el código, solo quien tiene acceso al servidor (terminal o logs) puede. Es el
mismo patrón de Jenkins o Grafana.
**Conceptos:**
- **`secrets`**: genera azar apto para seguridad (`random` es predecible). El alfabeto no tiene
  0/O ni 1/I/L para que el código se copie a mano sin errores.
- **Hashing**: solo se guarda la huella SHA-256 del código. Quien lea la base no puede saber cuál
  es. Para comparar se usa `hmac.compare_digest`, que tarda lo mismo acierte o no (así no se puede
  adivinar el código midiendo tiempos).
- **Comandos de gestión**: un archivo en `cuentas/management/commands/` con una clase `Command`. Se
  escribe con `self.stdout.write` y se falla con `CommandError` (código de salida 1).
- **Logging**: con `DEBUG=False`, Django no saca sus mensajes por consola, y Docker o systemd solo
  guardan lo que sale por stdout/stderr. Por eso `config/settings.py` define `LOGGING` con un handler
  `consola` (`StreamHandler`) sin el filtro `require_debug_true`. El nivel de Django se cambia con
  `NIVEL_LOG_DJANGO`. En las pruebas se callan los avisos 403/404 de `django.request`
  (`config/pruebas.py`), que ahora llenaban la salida.
- Se revisó que ningún log escriba contraseñas ni códigos: los avisos de correo solo llevan el id.

### Historia 2 · Enlace discreto en "Entrar"
**Qué se hizo:** mientras no hay un admin activo, Entrar muestra al final, tras una línea fina, el
enlace pequeño "¿Instalación nueva? Configurar la administración". No aparece en ninguna otra
página. La vista `entrar` le pasa a la plantilla `mostrar_configuracion_inicial`; la plantilla no
hace consultas.
**Conceptos:**
- **Caché**: para no preguntar a la base "¿hay admin?" en cada visita a Entrar, el resultado se
  guarda con `cache.get_or_set(clave, función, 60)`. Si la clave no existe, llama a la función y
  guarda el resultado 60 segundos.
- **Señales `post_save` y `post_delete`** (`cuentas/signals.py`): al guardar o borrar un usuario
  (activar o desactivar es guardar) o un `RolAsignado`, se borra ese valor. Así el enlace desaparece
  en cuanto se crea el admin.
- **Por qué además vence en 60 s:** la caché en memoria (`LocMemCache`) es de cada proceso. Con
  varios procesos de gunicorn, borrarla en uno no la borra en los otros, y `QuerySet.update()` no
  dispara señales. Por eso el valor dura poco y nunca decide el acceso: la página y la creación del
  admin consultan siempre la base, así que un enlace que se vea unos segundos de más lleva a un 404.

### Historia 3 · Asistente para crear el primer admin
**Qué se hizo:** `/configuracion-inicial/` tiene dos pasos: el código, con una ayuda plegable
(`<details>`) que explica dónde encontrarlo, y los datos del admin. Para el segundo paso hay dos
pestañas: crear una cuenta nueva o promover una que ya existe, que conserva sus roles. Al terminar,
la persona entra con el rol admin y el panel le muestra "Listo…" y tres siguientes pasos (correo de
envío, período actual, plan de estudios). Los pasos se muestran una sola vez: la vista guarda una
marca en la sesión y el panel la saca con `pop`. La lógica está en
`crear_primer_admin` (`cuentas/configuracion_inicial.py`), no en la vista. `createsuperuser` sigue
sirviendo y también deja "Configuración inicial" en el nuevo campo `CambioRol.motivo`.
**Conceptos:**
- **Transacción (`transaction.atomic`)**: todo o nada. Si algo falla a la mitad, no queda una
  cuenta sin rol.
- **`select_for_update()`**: bloquea la fila de `ConfiguracionInicial` hasta que termina la
  transacción. Si dos personas envían el formulario a la vez, la segunda espera. Cuando entra, vuelve
  a preguntar "¿hay admin?" **dentro** del bloqueo, ve que sí y recibe un 404. Así nunca se crean
  dos admins (condición de carrera).
- **Un error dentro de `atomic` deshace todo**, también el conteo de intentos fallidos. Por eso el
  servicio anota el fallo, deja que la transacción termine y lanza la excepción después.
- **Mensajes genéricos**: un código malo, una contraseña mala o un correo que no existe dan el mismo
  mensaje. Si el correo no existe, se calcula igual un hash de contraseña para que la respuesta tarde
  lo mismo. Además, el formulario de cuenta nueva quita la validación de correo único de Django
  (`validate_unique`), que le diría "ese correo ya existe" a alguien sin código.
- **Límite por IP**: se reutiliza `cuentas/limite.py` (5 fallos, 15 minutos de bloqueo).
- **Pestañas sin JavaScript**: son enlaces `?opcion=nueva` / `?opcion=existente` con
  `aria-current`, así funcionan con el teclado y sin JS.
- **`{% translate variable %}`**: el motivo se guarda en español (es un dato del historial) y se
  traduce al mostrarlo.

### Historia 4 · Qué pasa si se quedan sin admin
**Qué se hizo:** la regla de la 008 ("no se le quita el rol admin al último admin activo") ahora
cubre también desactivar y eliminar, en la app y en el panel de Django: el formulario de gestión y
el del admin de Django rechazan desactivarlo, `has_delete_permission` devuelve False para esa cuenta
(su página de eliminar da 403), la acción masiva "Eliminar seleccionados" se reemplaza por una que se
niega si no quedaría ningún admin, y la tabla de roles del admin no deja borrar ni cambiar la fila
admin. Si aun así no queda ningún admin (un cambio directo en la base), el enlace de Entrar y la
página vuelven, siempre con un código nuevo. El README lo explica en "Recuperar el acceso de
administrador".
**Conceptos:**
- **`BaseInlineFormSet.clean()`**: valida todas las filas de una tabla en línea juntas (por
  ejemplo, "¿queda alguna fila admin sin marcar para borrar?").
- **Acciones del admin**: `get_actions` devuelve un diccionario `{nombre: (función, nombre,
  descripción)}`. Se reemplaza `delete_selected` por una función que revisa la regla y, si se
  cumple, llama a la original de Django.
- **`has_delete_permission(request, obj)`**: con `obj` decide por objeto. Django oculta el botón y
  responde 403 si se entra a la URL a mano.
