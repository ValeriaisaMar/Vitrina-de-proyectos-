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

