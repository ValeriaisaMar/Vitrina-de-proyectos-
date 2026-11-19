# Vitrina de Proyectos

> Los proyectos de la UTEQ, revisados y verificados, en un solo lugar.

Vitrina de Proyectos es una aplicación web para que la universidad reúna y muestre los proyectos que hacen sus estudiantes. Los estudiantes los suben, los docentes los revisan y, cuando cumplen, quedan **verificados** y visibles para cualquiera que quiera conocer el trabajo de la UTEQ.

No es un ejercicio de clase: la app se construye para quedar en uso en la universidad una vez termine el curso.

**Estado del proyecto:** en desarrollo durante un curso intensivo de dos semanas (noviembre 2026).

## ¿Para qué sirve?

Hoy los proyectos de los estudiantes quedan dispersos: en repositorios personales, en una memoria USB o en el correo del docente. Cuando alguien quiere saber qué se hace en la universidad (un estudiante nuevo, un docente de otra carrera, una empresa o un visitante) no hay dónde verlo, ni forma de saber si un proyecto fue revisado de verdad.

Vitrina resuelve eso con tres cosas:

- **Un lugar único** donde quedan todos los proyectos, con su repositorio, tecnologías y documentación.
- **Un proceso de revisión claro**: cada proyecto pasa por un docente antes de mostrarse.
- **Un sello de verificación**: lo que aparece en la vitrina pública fue revisado y aprobado por la universidad.

## ¿Cómo funciona?

1. **Subida.** El estudiante registra su proyecto: descripción, tecnologías, enlace al repositorio y documentación.
2. **Evaluación automática.** El sistema calcula el Health Score del repositorio como apoyo para el revisor.
3. **Revisión docente.** Un docente o revisor lo revisa y decide:
   - **Verificar y publicar**: el proyecto entra a la vitrina pública con su sello.
   - **Devolver con observaciones**: el equipo lo corrige y lo vuelve a enviar.
   - **Enviar al Cementerio**: no se borra, pero queda marcado como abandonado o incompleto.
4. **Consulta.** Cualquier persona puede explorar los proyectos verificados con filtros por carrera, tecnología o año.

## Funcionalidades

### Núcleo

**Publicación de proyectos.** Los estudiantes suben sus proyectos con tecnologías, repositorio y documentación, y pueden editarlos mientras no estén verificados.

**Revisión docente.** El docente o revisor tiene una bandeja con los proyectos pendientes, deja observaciones y decide si se verifica, se devuelve o se envía al Cementerio.

**Vitrina pública.** Listado de proyectos verificados con búsqueda y filtros, abierto a visitantes sin necesidad de cuenta.

### Complementos

**Health Score.** Un puntaje de 0 a 100 que analiza el README, la licencia, las pruebas, las dependencias y la actividad del repositorio. Clasifica el proyecto como Vivo (verde), Dormido (amarillo) o Zombi (rojo). Ayuda al revisor, pero no reemplaza su decisión.

**Cementerio y Resurrección.** Los proyectos abandonados conservan su historia y el Cementerio explica qué les faltó. Otro equipo puede pulsar «Resucitar» y continuarlos.

**Árbol genealógico.** Cada proyecto muestra de dónde viene, qué continuaciones tuvo y cuántas generaciones lo siguieron.

**Comunidad.** Comentarios, calificaciones y adopción de proyectos entre estudiantes.

## Roles

| Rol | Qué puede hacer |
|---|---|
| Visitante | Explorar los proyectos verificados |
| Estudiante | Subir, editar y adoptar proyectos |
| Docente / revisor | Revisar, verificar y pedir correcciones |
| Administrador | Gestionar usuarios, carreras y categorías |

## Tecnologías

- **Python** y **Django 6.1**
- **PostgreSQL** como base de datos
- **Docker** para el despliegue

Las dependencias de Python están listadas en `requirements.txt`.

## Requisitos previos

- Python 3.12 o superior
- Git
- PostgreSQL
- Docker y Docker Compose (para el despliegue)

## Instalación local

Sigue estos pasos en orden desde una terminal.

1. Clona el repositorio y entra a la carpeta:

```bash
git clone https://github.com/ValeriaisaMar/Vitrina-de-proyectos-.git
cd Vitrina-de-proyectos-
```

2. Crea y activa un entorno virtual. En Windows con PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Crea la base de datos en PostgreSQL, por ejemplo desde `psql` o pgAdmin:

```sql
CREATE DATABASE vitrina_db;
```

5. Configura las variables de entorno. Copia el archivo de ejemplo y edítalo con tus datos:

```powershell
copy .env.example .env
```

En macOS o Linux usa `cp .env.example .env`. El archivo `.env` contiene tus credenciales, por eso no se sube al repositorio.

6. Aplica las migraciones para crear las tablas:

```bash
python manage.py migrate
```

7. Crea un superusuario para entrar al panel de administración:

```bash
python manage.py createsuperuser
```

8. Inicia el servidor de desarrollo:

```bash
python manage.py runserver
```

Abre `http://127.0.0.1:8000` en tu navegador. El panel de administración está en `http://127.0.0.1:8000/admin/`.

## Despliegue con Docker

> En preparación: el `Dockerfile` y el `docker-compose.yml` todavía no están en el repositorio.

La aplicación se desplegará en contenedores: uno para Django y otro para PostgreSQL. Cuando estén listos los archivos, la app se levantará con:

```bash
docker compose up --build
```

## Variables de entorno

El archivo `.env` necesita estas variables:

```
SECRET_KEY=cambia_esta_clave
DEBUG=True

DB_NAME=vitrina_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
```

Con Docker, `DB_HOST` debe ser el nombre del servicio de PostgreSQL en `docker-compose.yml` (por ejemplo `db`). En producción, `DEBUG` va en `False`.

## Estructura del proyecto

```
Vitrina-de-proyectos-/
├── config/              Configuración de Django (settings, urls, wsgi, asgi)
├── vitrina/             App principal: modelos, vistas, rutas y plantillas
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── manage.py            Utilidad de comandos de Django
├── requirements.txt     Dependencias de Python
├── .env.example         Plantilla de variables de entorno   (por crear)
├── Dockerfile           Imagen de la app                     (por crear)
├── docker-compose.yml   Servicios: app + PostgreSQL          (por crear)
└── README.md
```

Por ahora toda la lógica vive en la app `vitrina`. Si alguna parte crece mucho (por ejemplo el Health Score o la comunidad), se puede separar en su propia app.

## Flujo de trabajo del equipo

La rama `main` se mantiene estable. Cada funcionalidad se desarrolla en su propia rama (por ejemplo `feature/revision-docente`) y se integra mediante Pull Request. Los mensajes de commit siguen un estilo común, como `feat: agrega subida de proyectos` o `docs: actualiza README`.

## Sobre el proyecto

Vitrina de Proyectos nace en el curso intensivo de desarrollo web con Django y Docker de la UTEQ. La desarrollan tres estudiantes de la Universidad de Córdoba (Colombia), embajadores en movilidad académica, con una meta clara: dejarle a la UTEQ una herramienta funcionando, no solo un prototipo.

- Dayana Ayala Goez
- Abelardo Hernandez Ochoa
- Valeria Isabel Martinez Luna

## Licencia

Distribuido bajo licencia MIT. Consulta el archivo `LICENSE` para más información.
