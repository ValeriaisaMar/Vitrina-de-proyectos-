# Implementation Plan: Paneles por rol

**Branch**: `feature/006-paneles` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Una vista `panel` en `vitrina/paneles.py` que arma el resumen según el rol, y en `cuentas` la
gestión de usuarios para el admin (lista con filtros y edición de rol y estado).

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| V. Permisos | Solo `Rol.ADMIN` cambia roles (`@rol_requerido`), con reglas que impiden auto-bloquearse | ✅ |
| II. Consultas | Cifras con `aggregate`/`annotate` y `Count(filter=Q(...))`: pocas consultas por panel | ✅ |
| X. Interfaz | Barras en HTML con el número escrito; un solo tono verde; sin JavaScript | ✅ |
| VIII. Pruebas | Cada panel, cada regla de la gestión de usuarios | ✅ |

## Decisiones de diseño

1. **Una URL, tres paneles**: `/panel/` elige plantilla según `user.rol`; cada rol solo ve lo suyo.
2. **Cifras en la base de datos**: `Count("id", filter=Q(estado=...))` cuenta todos los estados
   en una sola consulta.
3. **Gestión de usuarios con un formulario pequeño** (`FormularioGestionUsuario`: rol y activo);
   las reglas (no a uno mismo, no a superusuarios) están en el formulario y se prueban ahí.
4. **Registro con `LogEntry`**: Django ya trae el registro de acciones del admin; se reutiliza y se
   ve en `/admin/` → Registro de acciones.
5. **Barras**: un solo tono (verde) porque miden cantidades de una sola serie; cada barra lleva su
   etiqueta y número, así nada depende solo del color.

## Project Structure

```text
vitrina/
├── paneles.py          panel (estudiante, profesor, admin)
├── urls.py             + panel/
├── templates/vitrina/paneles/  estudiante.html, profesor.html, admin.html, _cifra.html, _barras.html
└── tests/test_paneles.py
cuentas/
├── forms.py            + FormularioGestionUsuario
├── views.py            + usuarios, usuario_editar; activar redirige al panel
├── urls.py             + usuarios/, usuarios/<id>/
├── templates/cuentas/  usuarios.html, usuario_editar.html
└── tests/test_gestion_usuarios.py; test_entrar.py y test_registro.py (llegan al panel)
proyectos/views.py                  consultas_bandeja pasa a ser pública (la usa el panel del profesor)
proyectos/migrations/0004_codigos_faltantes.py  códigos para proyectos aprobados a mano en el 003
proyectos/tests/test_migracion_codigos.py
cuentas/tests/test_usuario.py       el inicio de sesión llega al panel
config/settings.py                  LOGIN_REDIRECT_URL = "vitrina:panel"
templates/parciales/encabezado.html "Mi panel" en el menú de cuenta
static/css/app.css · locale/en/LC_MESSAGES/django.po/.mo · README.md · APRENDIZAJE.md
```

> Ajuste durante la implementación: las capturas mostraron proyectos aprobados sin código (los que
> se aprobaron desde `/admin/` en el módulo 003, antes de existir la revisión). Se agregó la
> migración de datos `0004_codigos_faltantes` para completarlos con el mismo contador por año.

