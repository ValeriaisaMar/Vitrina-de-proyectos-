# Implementation Plan: Perfiles, profesor revisor elegido, período actual y navegación

**Branch**: `feat/009-perfiles-y-revisor` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

## Summary

Siete historias sobre las cuatro apps existentes, implementadas en orden de prioridad y una a la vez:
período actual único (`Periodo.es_actual`, período al enviar y al aprobar), arreglos rápidos (ayuda
del correo por proveedor, normalización NFC del texto, "Guardados"), planes de estudio
(`PlanEstudio`), perfiles públicos (`Perfil` y sus bloques), elección de revisor
(`SolicitudRevision` + sugerencias), menú del avatar con íconos SVG locales y detalles de portada.
Detalle de decisiones en [research.md](research.md); entidades en [data-model.md](data-model.md);
rutas en [contracts/rutas.md](contracts/rutas.md); pruebas a mano en [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.12+, Django 6.1.3
**Primary Dependencies**: las aprobadas (Django, psycopg, python-dotenv, qrcode, Pillow, reportlab, cryptography). **Ninguna nueva.**
**Storage**: PostgreSQL; archivos en `media/` (`MEDIA_ROOT`/`MEDIA_URL` ya configurados)
**Testing**: `python manage.py test` (paquete `tests/` de cada app), `mail.outbox`, `assertNumQueries`
**Target Platform**: navegador moderno, 360–1920 px, claro/oscuro, es/en
**Project Type**: aplicación web Django con plantillas y Tailwind standalone
**Performance Goals**: páginas de perfil, elección de revisor y menú con número fijo de consultas
**Constraints**: sin CDN; íconos SVG en el repo; funciona sin JavaScript (mejora progresiva)
**Scale/Scope**: decenas de profesores, cientos de estudiantes y proyectos

## Constitution Check

| Principio | Cómo se cumple | Estado |
| --- | --- | --- |
| I. Cuatro apps | `Perfil` y bloques en `cuentas`; `PlanEstudio`, `SolicitudRevision` en `proyectos`; perfil público en `vitrina`; nadie importa vistas ajenas | ✅ |
| II. Consultas seguras | Solo ORM; personas relacionadas y sugerencias con `annotate`/`values` agregados | ✅ |
| III. Entradas | Imágenes verificadas con Pillow y reprocesadas a webp; enlaces `http/https`; ORCID con dígito verificador | ⚠️ enmienda: 5 MB para foto y portada |
| V. Permisos | Revisión solo del profesor asignado; elegir revisor solo el creador; reasignar solo admin; todo en el servidor | ⚠️ enmienda: el admin ya no decide |
| VI. Integridad | Verificación y certificado muestran el período de aprobación; sin datos privados en el perfil (no correo) | ✅ |
| VII. Estados | Sin estados nuevos: subestados de Enviado deducidos de `SolicitudRevision`; `EventoEstado.accion` registra solicitudes; historial inmutable | ⚠️ enmienda: quién pasa Enviado → En revisión |
| VIII. Pruebas | Pruebas por historia (ver tasks) | ✅ |
| IX. Aprendizaje | Entrada en `APRENDIZAJE.md` por historia | ✅ |
| X. Interfaz | Íconos con `{% icono %}`; menú accesible; responsive; claro/oscuro | ✅ |
| XI. Idioma | Toda cadena en `.po` (edición a mano y compilación con script, no hay gettext en Windows) | ✅ |
| XII. Dependencias | Sin nuevas; `fontTools` solo como herramienta externa, las pruebas usan reportlab | ✅ |
| XIV. Flujo | Rama `feat/009-…` pedida por el equipo; commits los hace el equipo | ✅ |
| IA: migraciones | Solo migraciones nuevas, reversibles, con migración de datos | ✅ |

**Enmienda 3.0.0** (MAJOR: cambia reglas existentes): III (5 MB para foto de perfil y portada),
V y VII (el revisor lo elige el creador y lo acepta el profesor; solo el revisor asignado decide; el
admin reasigna). Se registra en el Sync Impact Report y queda para aprobación del equipo en el PR.

## Decisiones de diseño (resumen; detalle en research.md)

1. **Subestados de Enviado** en vez de estados nuevos: `Proyecto.subestado` se calcula con el revisor
   y la solicitud pendiente. La tabla `TRANSICIONES` cambia solo el "quién" de Enviado → En revisión
   (`REVISOR_ASIGNADO`).
2. **`EventoEstado.accion`** (`estado`, `solicitud`, `aceptada`, `no_aceptada`, `retirada`,
   `reasignada`): el flujo de solicitudes queda en el mismo historial inmutable.
3. **Servicios nuevos**: `proyectos/solicitudes.py` (solicitar, aceptar, no aceptar, retirar,
   reasignar, sugerir_profesores, profesores_elegibles) y `cuentas/perfiles.py` (personas relacionadas,
   búsqueda, validadores de enlaces). `cambiar_estado` sigue siendo la única puerta de los estados.
4. **Íconos**: SVG en `static/iconos/` (Tabler MIT + Simple Icons CC0), etiqueta `{% icono %}` en
   `vitrina/templatetags/iconos.py` registrada como *builtin*; lee el archivo una vez y lo cachea.
5. **Imágenes**: `config/imagenes.py` valida con Pillow (`verify` + reabrir), corrige orientación
   EXIF, recorta y guarda webp con `uuid4`.
6. **Período actual** con `UniqueConstraint(condition=Q(es_actual=True))` y cambio en una
   transacción; caché `periodo_actual` invalidada en `Periodo.save/delete`.
7. **Menú**: enlace a "Mi cuenta" (funciona sin JS) que `static/js/menu.js` convierte en botón con
   `aria-expanded`; la misma plantilla parcial sirve al menú y a la página.

## Project Structure

```text
config/
├── contexto.py          + periodo_actual, menu_cuenta (contadores con una consulta por tipo)
├── imagenes.py          (nuevo) validar y convertir imágenes a webp
└── settings.py          context processors y builtins de plantillas
cuentas/
├── models.py            + Perfil, Aptitud, ExperienciaLaboral, Estudio
├── perfiles.py          (nuevo) slug, relacionados, búsqueda, validadores GitHub/LinkedIn/ORCID
├── forms.py             + formularios de cada sección del perfil
├── correo_envio.py      + mensaje para 5.7.139 / 5.7.30
├── views.py · urls.py   + editar secciones del perfil, mi cuenta, disponibilidad, bienvenida
├── migrations/          0006+ perfiles (con datos)
└── templates/cuentas/   correo_envio (ayuda por proveedor), mi_cuenta, perfil_* parciales
proyectos/
├── models.py            Periodo.es_actual, PlanEstudio, Asignatura.plan, Proyecto (periodo nulo,
│                        periodo_aprobacion, imagen_portada, color_portada, video), SolicitudRevision,
│                        EventoEstado.accion
├── servicios.py         período al enviar/aprobar, REVISOR_ASIGNADO, bandeja solo del revisor
├── solicitudes.py       (nuevo) flujo de solicitudes y sugerencias
├── permisos.py · forms.py · views.py · urls.py · correos.py · admin.py
├── migrations/          0008+ (cada una con su migración de datos)
├── management/commands/recordar_solicitudes.py   (opcional)
└── templates/proyectos/ periodos, planes, enviar (elegir revisor), solicitudes, bandeja, correos
comunidad/               "Guardados" (vistas, URL nueva con redirección, plantillas, mensajes)
vitrina/
├── templatetags/iconos.py  (nuevo)
├── views.py             persona (perfil público), explorar con autores y bloque Personas
└── templates/vitrina/   persona, explorar, detalle (enlaces, portada), _tarjeta_proyecto, verificado
templates/parciales/     encabezado, menu_cuenta, pie (período actual)
static/iconos/ · static/js/menu.js · static/src/entrada.css · static/css/app.css
locale/en/LC_MESSAGES/   cadenas nuevas
README.md · APRENDIZAJE.md · .specify/memory/constitution.md · docs/sdd/constitucion.md
```

**Structure Decision**: se mantienen las cuatro apps; no se crean apps nuevas.

## Complexity Tracking

| Desviación | Por qué hace falta | Alternativa más simple descartada |
| --- | --- | --- |
| Enmienda de la constitución (III, V, VII) | El documento de la 009 cambia quién revisa y el tamaño de imagen | Mantener la regla vieja contradice lo pedido |
| `EventoEstado.accion` | Registrar solicitudes en el historial sin estados falsos | Una tabla aparte de historial duplicaría la línea de tiempo |
