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
