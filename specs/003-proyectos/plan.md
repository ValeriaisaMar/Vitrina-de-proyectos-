# Implementation Plan: Proyectos, explorar y detalle

**Branch**: `feature/003-proyectos` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

## Summary

Crear los modelos de la app `proyectos` (Asignatura, Tecnologia, Proyecto, Autoria, Imagen)
con su migración de datos (malla UTEQ y tecnologías), el formulario de proyecto con coautores,
imágenes y PDF, las vistas de crear, editar, eliminar y "Mis proyectos", y en la app `vitrina`
las páginas Explorar y Detalle y las cifras de la portada.

## Technical Context

**Language/Version**: Python 3.12+ · **Dependencies**: Django 6.1.3 y Pillow (ya aprobada; la usa `ImageField`)

**Storage**: PostgreSQL; archivos en `media/proyectos/` · **Testing**: `TestCase` con archivos en memoria

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| II. Consultas seguras | ORM con `Q`, `select_related`, `prefetch_related` y `distinct` | ✅ |
| III. Entradas no confiables | URL solo http/https; PDF verificado por cabecera; imágenes verificadas por Pillow; nombres generados | ✅ |
| V. Permisos por rol | `@rol_requerido("estudiante")` para crear; autoría y estado verificados en el servidor | ✅ |
| VI. Integridad | `Proyecto.objects.publicados()` es la única puerta de las páginas públicas | ✅ |
| VII. Estados | Solo se crea en Borrador; ningún cambio de estado en este módulo | ✅ |
| VIII. Pruebas | Un caso por escenario | ✅ |

## Decisiones de diseño

1. **Modelo completo desde ya**: `Proyecto` trae `codigo`, `revisor` y `aprobado_en` (vacíos)
   para que los módulos 004 y 005 no tengan que reestructurarlo.
2. **Autoría con modelo intermedio** (`Autoria`): permite marcar al creador y guardar la fecha.
3. **Manager con `publicados()`**: todas las consultas públicas pasan por ahí.
4. **Migración de datos** (`0002_datos_iniciales`): carga la malla y las tecnologías con
   `RunPython`; así cada equipo tiene los mismos datos sin pasos manuales.
5. **Validadores en `proyectos/validadores.py`**: tamaño y tipo del PDF (lee los primeros bytes
   `%PDF-`) y de las imágenes.
6. **Varias imágenes en un solo campo**: un `FileField` con un widget que permite seleccionar
   varios archivos (`allow_multiple_selected`), como recomienda la documentación de Django.
7. **Slug estable**: se genera al crear (`titulo` + número si se repite) y no cambia.
8. **Explorar** usa un formulario GET (`FormularioFiltros`) para validar los parámetros; la
   paginación usa la etiqueta `{% querystring %}` de Django para conservar los filtros.
9. **Detalle único** para público y vista previa: si no está aprobado, solo lo ven autores,
   profesores y admins; para los demás es 404 (no se revela que existe).

## Project Structure

```text
proyectos/
├── models.py          Asignatura, Tecnologia, Estado, Proyecto (+ manager), Autoria, Imagen
├── validadores.py     validar_pdf, validar_imagen, validar_periodo
├── forms.py           FormularioProyecto (coautores, imágenes, PDF)
├── permisos.py        puede_editar, puede_eliminar, puede_ver
├── views.py           mis_proyectos, crear, editar, eliminar
├── urls.py            app_name = "proyectos"
├── admin.py           Asignatura, Tecnologia, Proyecto (con autorías e imágenes)
├── migrations/        0001_initial, 0002_datos_iniciales
├── templates/proyectos/  mis_proyectos, formulario, confirmar_eliminar
└── tests/             utilidades.py, test_modelos.py, test_vistas.py (crear, editar, eliminar y permisos)
vitrina/
├── forms.py           FormularioFiltros
├── views.py           inicio (cifras y destacados), explorar, detalle
├── templates/vitrina/ explorar.html, detalle.html, _tarjeta_proyecto.html, inicio.html
└── tests/             test_explorar.py, test_detalle.py, test_portada.py
templates/parciales/encabezado.html   enlace "Mis proyectos" para estudiantes
vitrina/tests/test_paginas.py        Explorar ya no es "Próximamente"
cuentas/tests/test_permisos.py       la URLconf de prueba incluye proyectos/ (el encabezado la enlaza)
static/src/entrada.css               estilos de casillas tipo etiqueta
static/css/app.css                   CSS compilado
static/js/tema.js                    filtros de Explorar plegados en móvil
locale/en/LC_MESSAGES/django.po/.mo  textos nuevos en inglés
```

> Ajuste durante la implementación: las pruebas de crear, editar y permisos quedaron juntas en
> `test_vistas.py`, y se sumaron a la lista los archivos de apoyo que el módulo también toca.
