# Implementation Plan: Base de la plataforma

**Branch**: `feature/001-base-plataforma` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-base-plataforma/spec.md`

## Summary

Dejar el proyecto listo para que los demás módulos se construyan encima: configuración desde
`.env` con PostgreSQL, el usuario propio en la app `cuentas` (antes de la primera migración),
las cuatro apps creadas, la plantilla base con el estilo neo-brutalismo institucional compilado
con Tailwind, una portada animada, el cambio de idioma español/inglés, el modo claro/oscuro y
páginas de error con el mismo diseño.

## Technical Context

**Language/Version**: Python 3.12+ (probado con 3.13)

**Primary Dependencies**: Django 6.1.3, psycopg 3, python-dotenv. qrcode, Pillow y reportlab
quedan instalados para los módulos siguientes.

**Storage**: PostgreSQL 15+ (probado con 16)

**Testing**: `django.test.TestCase` con `python manage.py test`

**Target Platform**: servidor Linux o Windows; navegadores modernos de escritorio y celular

**Project Type**: aplicación web monolítica con plantillas en el servidor

**Performance Goals**: portada en menos de 2 s en red local; un solo CSS y un JS pequeño

**Constraints**: sin CDN (fuentes y CSS locales), sin Node, accesible (AA) y responsive de 360 a 1920 px

**Scale/Scope**: una carrera; decenas de usuarios a la vez

## Constitution Check

| Principio | Cómo se cumple en este módulo | Estado |
|---|---|---|
| I. Tecnología | Django 6.1, PostgreSQL, cuatro apps creadas | ✅ |
| II. Consultas seguras | Solo ORM; el gestor de usuarios usa `email__iexact` | ✅ |
| III. Entradas no confiables | Escapado automático; formularios con CSRF; idioma por POST | ✅ |
| IV. Autenticación segura | Correo único sin mayúsculas, validadores, cookies seguras en producción, tokens de 24 h | ✅ |
| V. Permisos por rol | Campo `rol` y propiedades `es_profesor` / `es_admin` listas para el 002 | ✅ |
| VIII. Pruebas | Pruebas en `cuentas/tests/` y `vitrina/tests/` | ✅ |
| IX. Código entendible | Vistas basadas en funciones, docstrings en español, `APRENDIZAJE.md` | ✅ |
| X. Interfaz | Tailwind standalone, tema en `static/src/entrada.css`, Unbounded + Archivo locales | ✅ |
| XI. Idioma | `LocaleMiddleware`, `{% translate %}`, `.po` y `.mo` en `locale/en/` | ✅ |
| XII. Dependencias | Solo las aprobadas, `requirements.txt` en UTF-8 | ✅ |
| XIII. Secretos | Todo sale de `.env`; error claro si falta algo | ✅ |

Sin desviaciones.

## Decisiones de diseño

1. **Usuario propio con `AbstractBaseUser` + `PermissionsMixin`** en vez de heredar de
   `AbstractUser`: así los campos quedan en español (`nombres`, `apellidos`, `rol`) y no queda
   un campo `username` que no se usa. El correo se guarda siempre en minúsculas y la búsqueda
   para iniciar sesión usa `email__iexact`.
2. **Configuración con `config/entorno.py`**: una función `variable()` lee de `.env` y, si falta
   algo obligatorio, lanza `ImproperlyConfigured` con un mensaje en español que nombra la
   variable. Se puede probar por separado.
3. **Correo con `MAILERS`** (la forma nueva de Django 6.1): SMTP de Gmail con TLS si hay
   contraseña de aplicación; si no, el correo se muestra en la consola.
4. **Tokens semánticos de color**: `entrada.css` define variables (`--fondo`, `--texto`,
   `--linea`, `--sombra`…) que cambian dentro de `.dark`, y Tailwind las expone como clases
   (`bg-fondo`, `text-texto`, `border-linea`). Así casi no hacen falta prefijos `dark:`.
5. **Componentes**: clases propias en `@layer components` (`.btn`, `.btn-primario`,
   `.tarjeta`, `.insignia`…) más plantillas incluibles para piezas con lógica
   (`componentes/campo.html`, `aviso.html`, `insignia_estado.html`, `boton.html`).
6. **Menú móvil con `<details>`**: funciona sin JavaScript (caso borde de la spec).
7. **Tema sin destello**: un script de 5 líneas en el `<head>` pone la clase `dark` antes de
   pintar; `static/js/tema.js` maneja el botón y el menú.
8. **Logo opcional**: un procesador de contexto busca `static/img/logo-uteq.svg` o `.png`; si
   no existe, se muestra el nombre en texto. Para poner el logo basta con copiar el archivo.
9. **Explorar y Verificar QR** muestran por ahora una página "Próximamente" con el diseño;
   sus módulos (003 y 005) la reemplazan.
10. **Inicio de sesión temporal**: se usan las vistas de autenticación de Django con una
    plantilla nueva. El registro viejo (`UserCreationForm`) se elimina porque no funciona con
    el usuario propio; el módulo 002 trae el registro con activación por correo.

## Project Structure

### Documentation (this feature)

```text
specs/001-base-plataforma/
├── spec.md
├── plan.md      (este archivo)
└── tasks.md
```

### Source Code

```text
config/
├── settings.py          lee .env; PostgreSQL; idiomas; MAILERS; seguridad
├── entorno.py           NUEVO: variable() y lista de valores
├── contexto.py          NUEVO: procesador de contexto (logo)
└── urls.py              admin, i18n, cuentas (temporal), vitrina
cuentas/                 NUEVA app
├── models.py            Usuario y Rol
├── managers.py          UsuarioManager
├── admin.py             UsuarioAdmin
├── forms.py             formularios del admin
├── migrations/0001_initial.py
└── tests/test_usuario.py, test_admin.py, test_entorno.py
proyectos/, comunidad/   NUEVAS apps vacías (apps.py, models.py, tests/)
vitrina/
├── views.py             inicio, explorar y verificar (próximamente)
├── urls.py              app_name = "vitrina"
├── templates/vitrina/inicio.html, proximamente.html
└── tests/test_paginas.py, test_idioma.py, test_errores.py
templates/
├── base.html, 404.html, 500.html
├── parciales/encabezado.html, pie.html, selector_idioma.html, mensajes.html
├── componentes/boton.html, campo.html, aviso.html, insignia_estado.html
└── registration/login.html
static/
├── src/entrada.css      tema de Tailwind
├── css/app.css          compilado
├── fonts/               Unbounded y Archivo (woff2) + licencias
├── js/tema.js
└── img/                 aquí va el logo
locale/en/LC_MESSAGES/django.po, django.mo
.env.example, requirements.txt, .gitignore, APRENDIZAJE.md
```

**Se eliminan**: `vitrina/templates/vitrina/base.html`,
`vitrina/templates/registration/login.html`, `vitrina/templates/registration/registro.html`,
`vitrina/static/vitrina/css/estilos.css`.

## Pruebas previstas

| Archivo | Qué comprueba |
|---|---|
| `cuentas/tests/test_entorno.py` | Variable obligatoria ausente da un error que la nombra; listas y booleanos se leen bien |
| `cuentas/tests/test_usuario.py` | Correo en minúsculas, único sin importar mayúsculas, rol por defecto, superusuario es admin, login con cualquier combinación de mayúsculas |
| `cuentas/tests/test_admin.py` | El admin lista, busca y edita usuarios |
| `vitrina/tests/test_paginas.py` | Portada con todas sus secciones, enlace para saltar al contenido, páginas "Próximamente", logo en texto cuando no hay archivo |
| `vitrina/tests/test_idioma.py` | Español por defecto, cambio a inglés por POST, idioma no soportado cae en español, sin textos en español al cambiar |
| `vitrina/tests/test_errores.py` | 404 y 500 con el diseño, en ambos idiomas y sin detalles técnicos |

Las pruebas visuales (anchos 360, 768, 1280 y 1920; contraste; tema sin destello) se hacen a
mano con la lista de `tasks.md`.
