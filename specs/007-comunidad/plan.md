# Implementation Plan: Comunidad

**Branch**: `feature/007-comunidad` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Modelos `MeGusta`, `Favorito` y `Comentario` en la app `comunidad`, vistas POST para cada acción,
la sección "Comunidad" en la ficha del proyecto, "Mis favoritos", y el conteo de me gusta en las
tarjetas y en el orden de Explorar.

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| III. Entradas | Comentario validado (2–1000 caracteres) y siempre escapado; límite de 5 cada 10 min | ✅ |
| V. Permisos | Ocultar: autores del proyecto y admins (`comunidad/permisos.py`); borrar: quien comentó | ✅ |
| VI. Integridad | Las acciones solo existen sobre `Proyecto.objects.publicados()` | ✅ |
| XV. Prioridad | Módulo independiente: si se quita, el núcleo no cambia | ✅ |

## Decisiones de diseño

1. **Me gusta y favorito como "interruptor"**: la misma URL agrega o quita; `UniqueConstraint`
   garantiza uno por persona aunque se pulse dos veces muy rápido.
2. **Ocultar, no borrar**: el moderador marca `oculto`, con quién y cuándo; se puede revertir.
3. **Formularios POST que redirigen a la ficha** (`#comunidad`): funcionan sin JavaScript.
4. **Conteos con `annotate`** en Explorar para no hacer una consulta por tarjeta.

## Project Structure

```text
comunidad/
├── models.py          MeGusta, Favorito, Comentario
├── migrations/        0001_initial
├── forms.py           FormularioComentario
├── permisos.py        puede_moderar, puede_borrar
├── consultas.py       datos_comunidad (lo que la ficha necesita)
├── views.py           me_gusta, favorito, comentar, ocultar, borrar, mis_favoritos
├── urls.py            app_name = "comunidad"
├── admin.py           Comentario con acción ocultar
├── templates/comunidad/  _seccion.html, favoritos.html
└── tests/             test_comunidad.py
config/urls.py                         + comunidad/
vitrina/views.py · forms.py            ficha con comunidad; orden "Más gustados"; conteo en tarjetas
vitrina/templates/vitrina/detalle.html, _tarjeta_proyecto.html
vitrina/tests/test_explorar.py         orden por me gusta
cuentas/tests/test_permisos.py         la URLconf de prueba incluye comunidad/ (el encabezado la enlaza)
templates/parciales/encabezado.html    "Mis favoritos" en el menú de cuenta
static/css/app.css · locale/en/LC_MESSAGES/django.po/.mo · README.md · APRENDIZAJE.md
```
