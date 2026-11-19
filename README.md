# Vitrina de Proyectos

> Ningún proyecto se pierde.

Vitrina de Proyectos es una plataforma web académica donde los estudiantes de Ingeniería de Software publican, verifican y reutilizan los proyectos que desarrollan en sus cursos, para continuar lo que ya se hizo en lugar de empezar de cero cada semestre.

**Estado del proyecto:** en desarrollo.

## El problema

Muchos proyectos universitarios se pierden al terminar el semestre. Cada curso vuelve a construir soluciones similares, nadie sabe si lo antiguo funciona o está completo, y se pierde la memoria de lo que ya se hizo. Este proyecto propone un lugar único para publicar, comprobar y reutilizar ese trabajo.

## ¿Cómo funciona?

Un estudiante sube su proyecto con sus tecnologías, el enlace al repositorio y la documentación. El sistema lo evalúa automáticamente con el Health Score y luego un docente lo revisa. Según el resultado, el proyecto queda publicado, se devuelve con observaciones para que lo corrijan o se envía al Cementerio. Una vez publicado, cualquier usuario puede consultarlo con filtros, comentarlo, calificarlo y adoptarlo para continuar su desarrollo.

## Funcionalidades principales

**Publicación y búsqueda.** Subida de proyectos con tecnologías, repositorio y documentación, y búsqueda por filtros para encontrar lo que ya existe.

**Health Score.** Una puntuación de 0 a 100 que analiza el README, la licencia, las pruebas, las dependencias y la actividad del repositorio. Según el puntaje, el proyecto se clasifica como Vivo (verde), Dormido (amarillo) o Zombi (rojo).

**Revisión docente.** El docente o revisor verifica cada proyecto y decide si se publica, se devuelve con observaciones o se envía al Cementerio.

**Cementerio y Resurrección.** Los proyectos abandonados no se borran: conservan su historia y el Cementerio explica qué les faltó. Otro equipo puede pulsar «Resucitar» y continuarlos.

**Árbol genealógico.** Cada proyecto muestra de dónde viene, qué continuaciones tuvo, cuántas generaciones lo siguieron y cuál fue su impacto.

**Comunidad.** Comentarios, calificaciones y adopción de proyectos entre estudiantes.

## Roles

El sistema maneja cuatro roles. El **visitante** consulta proyectos verificados. El **estudiante** publica, edita y adopta proyectos. El **docente/revisor** verifica y solicita correcciones. El **administrador** gestiona usuarios y categorías.

## Tecnologías

El proyecto está desarrollado en Python con el framework Django y usa PostgreSQL como base de datos. Las dependencias están listadas en `requirements.txt`.

## Requisitos previos

Antes de instalar necesitas tener Python 3.12 o superior, Git y PostgreSQL instalados en tu computador.

## Instalación

Sigue estos pasos en orden desde una terminal.

1. Clona el repositorio y entra a la carpeta:

```bash
git clone https://github.com/ValeriaisaMar/Vitrina-de-proyectos-.git
cd Vitrina-de-proyectos-
```

2. Crea y activa un entorno virtual. En Windows con PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

En macOS o Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Crea la base de datos en PostgreSQL, por ejemplo desde `psql` o pgAdmin:

```sql
CREATE DATABASE vitrina_db;
```

5. Configura las variables de entorno. Copia el archivo de ejemplo y edítalo con tus datos de PostgreSQL:

```bash
copy .env.example .env
```

En macOS o Linux usa `cp .env.example .env`. El archivo `.env` contiene tus credenciales, por eso no se sube al repositorio.

6. Aplica las migraciones para crear las tablas:

```bash
python manage.py migrate
```

7. Inicia el servidor de desarrollo:

```bash
python manage.py runserver
```

Abre `http://127.0.0.1:8000` en tu navegador y verás la aplicación funcionando.

## Variables de entorno

El archivo `.env` necesita estas variables:

```
DB_NAME=vitrina_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
```

## Estructura del proyecto

```
Vitrina-de-proyectos-/
├── config/            Configuración de Django (settings, urls)
├── docs/              Documentación del proyecto
│   └── img/           Capturas y diagramas
├── manage.py          Utilidad de comandos de Django
├── requirements.txt   Dependencias de Python
├── .env.example       Plantilla de variables de entorno
└── README.md
```

A medida que se agreguen las aplicaciones de Django (usuarios, proyectos, revisión, cementerio y comunidad), cada una tendrá su propia carpeta en la raíz.

## Documentación

La documentación detallada vive en la carpeta [`docs/`](docs/): descripción general, requisitos funcionales y no funcionales por rol, casos de uso, modelo de datos y diagramas.

## Flujo de trabajo del equipo

La rama `main` se mantiene estable. Cada funcionalidad se desarrolla en su propia rama (por ejemplo `feature/health-score`) y se integra mediante Pull Request. Los mensajes de commit siguen un estilo común, como `feat: agrega subida de proyectos` o `docs: actualiza README`.

## Equipo

Proyecto del curso de Ingeniería de Software, Universidad de Córdoba.

- Dayana Ayala Goez
- Abelardo Hernandez Ochoa
- Valeria Isabel Martinez Luna

## Licencia

Distribuido bajo licencia MIT. Consulta el archivo `LICENSE` para más información.
