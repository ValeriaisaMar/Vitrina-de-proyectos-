# Vitrina de Proyectos · UTEQ

> Los proyectos de Ingeniería de Software, revisados por docentes y verificables con un QR.

Vitrina de Proyectos es la plataforma web donde los estudiantes de **Ingeniería de Software** de
la **Facultad de Ciencias de la Computación de la Universidad Técnica Estatal de Quevedo (UTEQ)**
publican sus proyectos. Un docente los revisa y, cuando cumplen, quedan **verificados**: reciben
un código único, un QR y un certificado en PDF que cualquier persona puede comprobar.

No es un ejercicio de clase: la app se construye para quedar en uso en la carrera cuando termine
el curso.

**Estado:** en desarrollo durante un curso intensivo (noviembre de 2026).

---

## ¿Qué problema resuelve?

Hoy los proyectos de los estudiantes quedan dispersos en repositorios personales, memorias USB o
el correo del docente. Quien quiere conocer lo que se hace en la carrera (un estudiante nuevo, un
docente, una empresa que busca practicantes) no tiene dónde verlo ni cómo saber si un proyecto
fue revisado de verdad.

Vitrina lo resuelve con tres cosas:

- **Un lugar único** con cada proyecto, su repositorio, tecnologías, imágenes y documento.
- **Una revisión clara**: cada proyecto pasa por un docente, y cada paso queda en un historial.
- **Un sello comprobable**: el código `VP-AAAA-NNNN` y su QR llevan a una página pública que
  confirma quién lo aprobó y cuándo.

## Cómo funciona

```
Borrador ─► Enviado ─► En revisión ─┬─► Aprobado (público, con QR y certificado)
               ▲                    ├─► Rechazado (queda archivado)
               │                    └─► Con observaciones
               │                               │
               └──── el autor corrige y reenvía┘
```

1. **El estudiante sube su proyecto**: resumen, descripción, coautores, asignatura, tecnologías,
   repositorio, proyecto desplegado, video, portada, imágenes y PDF.
2. **Lo envía a revisión y elige al profesor** que lo revisará, con sugerencias que explican por
   qué aparecen. El proyecto toma el período académico actual.
3. **El profesor acepta la solicitud** (o no, y puede recomendar a otro) y decide: aprobar, pedir
   cambios o rechazar. Si pide cambios o rechaza, deja un comentario obligatorio. Al reenviar con
   observaciones, el proyecto vuelve al mismo profesor.
4. **Si se aprueba**, aparece en la vitrina pública con su sello, y los autores pueden descargar
   el QR y el certificado.

## Funcionalidades

| Módulo | Qué incluye |
|---|---|
| 001 Base | Configuración con `.env`, PostgreSQL, diseño base, modo claro/oscuro, español e inglés |
| 002 Cuentas | Registro con activación por correo, inicio de sesión seguro, recuperación de contraseña, perfil |
| 003 Proyectos | Crear y editar proyectos con coautores, explorar con búsqueda y filtros, detalle |
| 004 Revisión | Bandeja de profesores, decisiones con comentario, historial de estados |
| 005 Verificación | Código `VP`, QR descargable, certificado PDF y página pública de verificación |
| 006 Paneles | Panel del estudiante, del profesor y de administración (usuarios y roles) |
| 007 Comunidad | Me gusta, guardados (privados) y comentarios que pueden ocultar los autores del proyecto y el admin |
| 008 Ajustes del profesor | Varios roles por persona con selector "Entrar como", periodos académicos administrables, correo de envío configurable desde la app, respuestas del autor en los comentarios e identidad visual completa (logos, sellos, favicon, vista previa al compartir) |
| 009 Perfiles y revisor | Un solo período actual, plan de estudios administrable, perfil público de cada persona, el estudiante elige al profesor revisor (sugerencias, solicitudes, reasignación), menú de la cuenta con íconos, portada y color del proyecto, enlaces a demo y video |

## Roles

| Acción | Visitante | Estudiante | Profesor | Admin |
|---|:-:|:-:|:-:|:-:|
| Ver la vitrina y verificar un QR | ✓ | ✓ | ✓ | ✓ |
| Ver perfiles públicos | ✓ | ✓ | ✓ | ✓ |
| Dar me gusta, comentar y guardar proyectos | | ✓ | ✓ | ✓ |
| Crear y editar sus proyectos (antes de aprobarse) y elegir revisor (el creador) | | ✓ | | |
| Aceptar solicitudes y revisar: aprobar, pedir cambios o rechazar | | | ✓ (asignado) | |
| Reasignar el revisor de un proyecto | | | | ✓ |
| Ocultar y responder comentarios de sus proyectos | | ✓ (autor) | | ✓ (ocultar) |
| Dar y quitar roles, período actual, plan de estudios y correo de envío | | | | ✓ |

Toda cuenta nueva es de estudiante. Un admin le da o le quita roles, y **una persona puede tener
varios** (por ejemplo, estudiante y admin). Quien tiene más de uno lo cambia con un clic en el menú de su
avatar (**Cambiar de rol**); lo que ve y puede hacer depende de ese **rol activo**, que siempre se
muestra en el encabezado. Al iniciar sesión se usa el último rol con el que entró. Nadie revisa un proyecto
del que es autor.

## Tecnologías

- **Python 3.12+** y **Django 6.1**: aplicación monolítica con plantillas en el servidor.
- **PostgreSQL**: base de datos.
- **Tailwind CSS**: compilado con el ejecutable standalone, sin Node.
- **qrcode + Pillow**: generación del QR. **reportlab**: certificado PDF.
- **python-dotenv**: lectura de la configuración desde `.env`.
- **Gmail SMTP**: correos de activación y recuperación.

**Diseño:** neo-brutalismo institucional con los colores de la UTEQ (verde `#025a27` y
amarillo `#ecb932`), tipografías Unbounded y Archivo, responsive y accesible.

## Arquitectura

```
Navegador (HTML + Tailwind + JS mínimo)
        │
Django · proyecto config
 ├── cuentas     usuario, registro, activación, login, recuperación, roles
 ├── proyectos   proyectos, estados, historial, revisión, QR y certificado
 ├── comunidad   me gusta, guardados, comentarios
 └── vitrina     inicio, explorar, detalle, verificación pública
        │
PostgreSQL · carpeta media (imágenes y PDF) · Gmail SMTP
```

Todos los cambios de estado pasan por una sola función, `proyectos/servicios.py →
cambiar_estado()`, que valida el permiso y registra el historial. Las reglas completas están en
la [constitución](.specify/memory/constitution.md).

## Estructura del repositorio

```
Vitrina-de-proyectos-/
├── config/                 settings (lee .env) y urls principales
├── cuentas/                app de usuarios y autenticación
├── proyectos/              app principal: proyectos, revisión, QR y PDF
├── comunidad/              app de interacción
├── vitrina/                app de páginas públicas
├── templates/              base.html y componentes reutilizables
├── static/
│   ├── src/entrada.css     tema de Tailwind (colores, fuentes, modo oscuro)
│   ├── css/app.css         CSS compilado (sí se sube)
│   └── js/                 tema, menú móvil y animaciones
├── locale/en/              traducciones al inglés
├── specs/                  especificaciones SDD por módulo
├── docs/sdd/               hoja de ruta y notas del proceso
├── APRENDIZAJE.md          bitácora de lo aprendido en cada tarea
├── .env.example            plantilla de configuración
└── requirements.txt
```

## Instalación local

### Requisitos previos

- Python 3.12 o superior
- PostgreSQL 15 o superior
- Git

### Pasos

1. Clona el repositorio y entra a la carpeta:

   ```bash
   git clone https://github.com/ValeriaisaMar/Vitrina-de-proyectos-.git
   cd Vitrina-de-proyectos-
   ```

2. Crea y activa un entorno virtual.

   Windows (PowerShell):

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   macOS o Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Crea la base de datos en PostgreSQL (desde `psql` o pgAdmin):

   ```sql
   CREATE DATABASE vitrina_db;
   ```

5. Copia la plantilla de configuración y complétala con tus datos:

   ```powershell
   copy .env.example .env      # Windows
   ```

   ```bash
   cp .env.example .env        # macOS o Linux
   ```

6. Crea las tablas y un administrador:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. Inicia el servidor:

   ```bash
   python manage.py runserver
   ```

   Abre `http://127.0.0.1:8000`. El panel de Django está en `/admin/`.

   Para probar el registro sin correo real, deja `EMAIL_HOST_PASSWORD` vacío: el correo de
   activación aparece en la terminal donde corre el servidor y puedes copiar el enlace de ahí.

   Las asignaturas de la malla y las tecnologías se cargan solas con `migrate`. Las imágenes y
   los PDF que suban los estudiantes se guardan en la carpeta `media/`, que no se sube a Git.
   El superusuario que creaste con `createsuperuser` es admin. Para nombrar profesores: entra
   con él → **Mi panel** → **Gestionar usuarios** → elige la cuenta → marca el rol **Profesor**.
   Al iniciar sesión, cada persona llega al panel de su rol activo (estudiante, profesor o admin).
   La migración crea el periodo académico del semestre actual y lo deja como **período actual**;
   los demás se crean en **Mi panel** → **Periodos académicos** (ahí se marca cuál es el actual).

### Si ya tenías el proyecto y bajas la versión 008

```bash
git pull
pip install -r requirements.txt          # agrega cryptography
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#   → copia el resultado en tu .env como CLAVE_CIFRADO=...
python manage.py migrate                 # roles múltiples, periodos, correo y respuestas
python manage.py compilemessages         # solo si tienes gettext; el .mo ya viene compilado
python manage.py runserver
```

Tus datos se conservan: cada usuario queda con el rol que tenía y cada proyecto con su periodo
(los periodos "AAAA-1"/"AAAA-2" se convierten en periodos ordinarios con ese nombre).

### Si ya tenías el proyecto y bajas la versión 009

```bash
git pull
pip install -r requirements.txt          # sin dependencias nuevas
python manage.py migrate                 # período actual, planes, perfiles, solicitudes, portadas
python manage.py compilemessages         # solo si tienes gettext; el .mo ya viene compilado
python manage.py runserver
```

- **No hay variables de entorno nuevas.** Los íconos (`static/iconos/`, Tabler Icons y Simple
  Icons, licencias en `static/iconos/LICENCIAS.txt`) y las fuentes ya vienen en el repositorio.
- **Qué hacen las migraciones con tus datos:** el periodo abierto más reciente queda como
  **período actual**; los aprobados guardan su período de aprobación; las asignaturas pasan al plan
  "Plan vigente"; cada usuario recibe su perfil público; los proyectos que estaban en revisión
  conservan su profesor; los enviados sin revisor quedan "Por asignar revisor" (su creador ve un
  aviso en el panel); "Favoritos" pasa a llamarse "Guardados"; y la primera captura de cada
  proyecto se convierte en su portada. No se pierde ningún proyecto, autoría, evento, comentario
  ni guardado.
- **Carpeta `media/`:** las fotos de perfil (`media/perfiles/fotos/`) y las portadas
  (`media/proyectos/portadas/`) se guardan ahí, convertidas a webp con nombres aleatorios. En
  desarrollo las sirve Django (`DEBUG=True`, ver `config/urls.py`); en producción las debe servir
  el servidor web (por ejemplo, nginx con `location /media/`). La carpeta no se sube a Git.
- **Recordatorio de solicitudes (opcional):** `python manage.py recordar_solicitudes` avisa a
  los profesores que llevan 3 días sin responder. Prográmalo una vez al día (Programador de tareas
  de Windows o cron).

## Variables de entorno

```ini
SECRET_KEY=cambia_esta_clave
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=vitrina_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=vitrinadeproyectosuteq@gmail.com
EMAIL_HOST_PASSWORD=contraseña_de_aplicación_de_gmail

SITIO_URL=

CLAVE_CIFRADO=clave_fernet_de_44_caracteres
```

- `EMAIL_HOST_PASSWORD` es una **contraseña de aplicación** de Google, no la contraseña normal
  de la cuenta. Se crea en la cuenta de Google después de activar la verificación en dos pasos.
- Si dejas el correo vacío en desarrollo, los correos se muestran en la terminal en lugar de
  enviarse.
- En producción, `DEBUG` va en `False` y `ALLOWED_HOSTS` lleva el dominio real.
- `CLAVE_CIFRADO` cifra la contraseña del correo que un admin guarda desde la app (ver
  [Correo de envío](#correo-de-envío)). Genera una con
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
  Si la cambias, la contraseña guardada ya no se puede leer y hay que volver a escribirla.
- `SITIO_URL` es opcional: es la dirección que va dentro de los QR. Vacía, se usa la dirección con
  la que entras. Para que un celular abra el QR durante la demo, conecta ambos a la misma red,
  pon la IP del portátil (`SITIO_URL=http://192.168.1.20:8000`), agrégala a `ALLOWED_HOSTS` y
  arranca con `python manage.py runserver 0.0.0.0:8000`. Un QR que apunta a `127.0.0.1` solo
  abre en el mismo portátil.

Para generar una `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

## Correo de envío

Un admin puede cambiar desde la app la cuenta que envía los correos: **Mi panel → Correo de
envío**. Tiene configuración rápida para Gmail y Outlook/Office 365, un botón **Probar
configuración** (envía un correo de prueba al admin sin guardar nada) y una tarjeta con el estado.

- La contraseña de aplicación se guarda **cifrada** con `CLAVE_CIFRADO` y nunca se vuelve a mostrar;
  dejar el campo vacío conserva la anterior.
- Si nadie la ha configurado, todo sigue como antes: Gmail con los datos del `.env` o, sin
  contraseña, la terminal.

## Identidad visual

Los logos, los sellos de la Facultad y de la Carrera, el favicon y la imagen para compartir ya
están en `static/img/` (qué va dónde: [LEEME-identidad.md](LEEME-identidad.md)). El encabezado
usa el logo verde en modo claro y el blanco en modo oscuro; el certificado PDF usa las versiones
PNG de `static/img/marca/`, porque reportlab no lee SVG ni WEBP. Si consiguen el logo oficial en
SVG, cópienlo como `static/img/logo-uteq.svg` y la plataforma lo usará.

## Estilos con Tailwind

El CSS compilado (`static/css/app.css`) está en el repositorio, así que **no necesitas Tailwind
para ver la app**. Solo lo necesitas si vas a cambiar estilos:

1. Descarga el ejecutable standalone de Tailwind para tu sistema desde su página de
   lanzamientos en GitHub (`tailwindcss-windows-x64.exe`, `tailwindcss-macos-arm64` o
   `tailwindcss-linux-x64`) y guárdalo en la raíz del proyecto (está en `.gitignore`).
2. Déjalo vigilando los cambios mientras trabajas:

   ```bash
   ./tailwindcss -i static/src/entrada.css -o static/css/app.css --watch
   ```

3. Antes de hacer commit, genera la versión final:

   ```bash
   ./tailwindcss -i static/src/entrada.css -o static/css/app.css --minify
   ```

## Idiomas

La interfaz está en español e inglés. Las traducciones compiladas (`.mo`) están en el
repositorio, así que no hace falta nada extra para usarlas. Si agregas o cambias textos:

```bash
python manage.py makemessages -l en
# edita locale/en/LC_MESSAGES/django.po
python manage.py compilemessages
```

Estos dos comandos necesitan GNU gettext instalado en tu equipo.

## Pruebas

```bash
python manage.py test
```

Cada app tiene su carpeta `tests/`. Se prueban los permisos de cada rol en cada página, todos
los cambios de estado, los correos y los archivos generados (QR y PDF). Ningún módulo se entrega
si las pruebas no pasan.

Las pruebas usan un ejecutor propio (`config/pruebas.py`): vacía la caché antes de cada prueba y
usa un hasher de contraseñas rápido, así la suite completa corre en menos de un minuto.

## Cómo trabajamos: desarrollo guiado por especificaciones (SDD)

Usamos [Spec Kit](https://github.com/github/spec-kit) con cuatro fases por módulo:

1. **Constitución**: reglas que no se negocian ([ver](.specify/memory/constitution.md)).
2. **Spec** (`specs/NNN-modulo/spec.md`): qué debe hacer el módulo y cómo se comprueba.
3. **Plan** (`plan.md`): cómo se construye: modelos, vistas, archivos.
4. **Tareas** (`tasks.md`): pasos pequeños y verificables, en orden.

La hoja de ruta con los módulos y las fechas está en
[`docs/sdd/hoja-de-ruta.md`](docs/sdd/hoja-de-ruta.md).

### Ramas y commits

- `main` siempre estable. Cada módulo en su rama: `feature/001-base-plataforma`,
  `feature/002-cuentas`, etc.
- Integración mediante Pull Request, con las pruebas en verde.
- Prefijos de commit: `feat:`, `fix:`, `docs:`, `test:`, `style:`, `refactor:`.
  Ejemplo: `feat: agrega activación de cuenta por correo`.

## Despliegue

El despliegue con Docker está fuera del alcance de esta etapa y se añadirá en una versión
posterior.

## Equipo

Desarrollado en el curso intensivo de desarrollo web de la UTEQ por tres estudiantes de la
Universidad de Córdoba (Colombia), embajadores en movilidad académica:

- Dayana Ayala Goez
- Abelardo Hernández Ochoa
- Valeria Isabel Martínez Luna

## Licencia

Por definir con la UTEQ, ya que la plataforma quedará en uso en la universidad.
