# Implementation Plan: Revisión e historial

**Branch**: `feature/004-revision` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Agregar a la app `proyectos` el historial (`EventoEstado`), el contador de códigos
(`Consecutivo`) y el servicio `cambiar_estado`; las vistas de enviar, bandeja, tomar y revisar;
el correo de decisión; y en el detalle, la observación destacada y la línea de tiempo.

## Technical Context

**Language/Version**: Python 3.12+ · **Dependencies**: ninguna nueva

**Storage**: PostgreSQL (bloqueo de filas con `select_for_update`) · **Testing**: `TestCase` y `mail.outbox`

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| V. Permisos por rol | `@rol_requerido` en bandeja y revisión; el servicio vuelve a comprobar el permiso | ✅ |
| VI. Integridad | Solo `cambiar_estado` aprueba; el admin de Django deja esos campos de solo lectura | ✅ |
| VII. Estados e historial | Tabla `TRANSICIONES` única; eventos inmutables; `PROTECT` impide borrar proyectos con historial | ✅ |
| VIII. Pruebas | Cada transición permitida y prohibida, cada permiso y el correo | ✅ |
| XIII. Secretos | El correo usa la configuración existente de `.env` | ✅ |

## Decisiones de diseño

1. **Un solo servicio**: `cambiar_estado(proyecto, nuevo, actor, comentario)` devuelve el evento o
   lanza `TransicionNoPermitida`, `PermissionDenied` o `ValidationError`. Las vistas solo lo llaman.
2. **Tabla de transiciones como datos**: un diccionario `(desde, hacia) → quién`. Leerla es leer la
   regla de la constitución.
3. **Bloqueo de fila**: `select_for_update()` dentro de `transaction.atomic()` evita que dos
   profesores tomen el mismo proyecto.
4. **Código con contador por año** (`Consecutivo`): se bloquea la fila del año, se suma uno y se
   guarda. Más claro y seguro que "buscar el último código y sumarle uno".
5. **Historial inmutable**: `EventoEstado.save()` rechaza modificar un evento existente y
   `delete()` está bloqueado; en el admin, solo lectura. `on_delete=PROTECT` hacia proyecto y actor.
6. **Correo después de guardar**: la vista envía el aviso cuando la decisión ya está guardada; si
   falla, se registra y no se deshace nada.
7. **La revisión es una página propia** (`/proyectos/<slug>/revisar/`) con la ficha, el historial y
   el formulario de decisión; el detalle público no cambia para los visitantes.

## Project Structure

```text
proyectos/
├── models.py          + EventoEstado, Consecutivo; Proyecto.ultima_observacion
├── servicios.py       TRANSICIONES, puede_cambiar, cambiar_estado, generar_codigo
├── correos.py         avisar_decision
├── forms.py           + FormularioEnvio, FormularioDecision
├── permisos.py        + puede_ver_historial
├── views.py           + enviar, bandeja, tomar, revisar
├── urls.py            + revision/, <slug>/enviar/, <slug>/tomar/, <slug>/revisar/
├── admin.py           estado y aprobación de solo lectura; historial en línea; EventoEstado de solo lectura
├── migrations/        0003_eventoestado_consecutivo
├── templates/proyectos/   enviar.html, bandeja.html, revisar.html, _historial.html,
│                          mis_proyectos.html (acción Enviar)
├── templates/proyectos/correos/   decision.txt, decision.html, decision_asunto.txt
└── tests/             test_servicios.py, test_revision.py
vitrina/
├── views.py           detalle: historial, observación y enlace a revisión
├── templates/vitrina/detalle.html
└── tests/test_detalle.py
templates/parciales/encabezado.html   enlace "Bandeja" para profesores y admins; menú de cuenta
static/css/app.css · locale/en/LC_MESSAGES/django.po/.mo · README.md · APRENDIZAJE.md
```

> Ajuste durante la implementación: con el botón "Bandeja" el encabezado ya no cabía en 1280 px.
> El saludo y "Cerrar sesión" pasaron a un menú de cuenta, y la navegación completa se muestra
> desde 1280 px (antes 1024); por debajo se usa el menú desplegable.

