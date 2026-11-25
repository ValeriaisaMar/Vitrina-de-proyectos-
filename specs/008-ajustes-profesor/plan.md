# Implementation Plan: Ajustes pedidos por el profesor

**Branch**: `feature/008-ajustes-profesor` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Cinco historias sobre las apps existentes: roles múltiples con rol activo en la sesión, modelo
`Periodo`, backend de correo configurable con contraseña cifrada, respuestas de autores en los
comentarios e integración del paquete de identidad visual. Incluye además dos cambios que venían
de antes y no se habían aplicado: un coautor puede salir del proyecto y el creador puede
transferirlo a un coautor.

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| I. Cuatro apps | `RolAsignado` y `ConfiguracionCorreo` en `cuentas`, `Periodo` en `proyectos`; `vitrina` solo importa modelos y servicios | ✅ |
| V. Permisos | Rol activo comprobado en el servidor (`rol_requerido`, `permisos.py`, `servicios._cumple`); sesión manipulada ignorada | ✅ |
| VI. Integridad | Conflicto de interés: un autor no revisa su proyecto; el periodo es `PROTECT` | ✅ |
| VII. Estados | Los cambios de estado siguen pasando solo por `servicios.cambiar_estado` | ✅ |
| XII. Dependencias | `cryptography` aprobada por el equipo; constitución 2.1.0 | ✅ |
| XIII. Secretos | `CLAVE_CIFRADO` en `.env`; la contraseña del correo se guarda cifrada | ✅ |
| Restricción de la IA: migraciones | Solo migraciones nuevas. `validar_periodo` se conserva porque la 0001 la importa | ✅ |

## Decisiones de diseño

1. **`es_estudiante`, `es_profesor`, `es_admin` = rol activo.** Las plantillas no cambian de
   significado; para "tiene el rol" se usa `tiene_rol()`. `es_docente` agrupa profesor y admin.
2. **Rol activo en la sesión, validado en cada petición.** El middleware nunca confía en la sesión:
   si el rol ya no está en `RolAsignado`, cae al rol por defecto.
3. **Servicio único para roles** (`cuentas/roles.py`), como `servicios.cambiar_estado`: reglas
   (al menos un rol, último admin) y registro en un solo lugar, con bloqueo de filas.
4. **Migraciones en tres pasos** para roles y periodos: campo nuevo → datos → quitar el viejo. Cada
   paso es reversible.
5. **Backend propio sobre `MAILERS`** (`config/correo.py`): decide en cada envío entre la
   configuración de la app y el respaldo del `.env`; la caché se invalida al guardar.
6. **Respuestas con `Prefetch(to_attr="hilo")`** y los ids de autores calculados una vez: sin N+1.
7. **Logos con `<picture>`** (webp + png) y `dark:hidden` / `hidden dark:block` para el modo oscuro.

## Project Structure

```text
cuentas/
├── models.py            Usuario (ultimo_rol, roles, rol_activo, tiene_rol), RolAsignado, CambioRol, ConfiguracionCorreo
├── roles.py             asignar_roles, dar_rol, validar_roles, activar_rol (servicio)
├── cifrado.py           Fernet con CLAVE_CIFRADO
├── correo_envio.py      probar, guardar, mensajes de error
├── managers.py          create_user(rol|roles), create_superuser → admin
├── forms.py             FormularioGestionUsuario (casillas), FormularioCorreoEnvio
├── views.py             cambiar_rol, usuario_editar, perfil, correo_envio
├── admin.py             roles en línea, CambioRol de solo lectura
├── migrations/          0002–0004 roles, 0005 configuración de correo
└── templates/cuentas/   usuarios, usuario_editar, perfil, correo_envio, _sello
config/
├── middleware.py        RolActivoMiddleware
├── contexto.py          roles(); marca() con logo claro/oscuro y webp
├── correo.py            CorreoConfigurableBackend, url_logo_correo
└── settings.py          MAILERS con respaldo, CLAVE_CIFRADO
proyectos/
├── models.py            Periodo, Proyecto.periodo FK
├── servicios.py         rol activo, conflicto de interés, bandeja sin proyectos propios
├── permisos.py          acciones de autor solo como estudiante
├── forms.py             periodos abiertos, FormularioPeriodo
├── views.py             periodos (lista, crear/editar, abrir/cerrar, borrar)
├── migrations/          0005–0007 periodos
└── templates/proyectos/ periodos, periodo_formulario, revisar (aviso de conflicto)
comunidad/
├── models.py            Comentario.respuesta_a (+ migración 0002)
├── permisos.py          puede_responder
├── consultas.py         hilo con Prefetch, es_de_autor
├── views.py · urls.py   responder
├── correos.py           aviso de respuesta
└── templates/comunidad/ _seccion, _comentario, correos/respuesta*
vitrina/                 paneles por rol activo, filtro de periodo por slug, OG del detalle, logo y sellos en verificación y PDF
templates/               base (iconos), encabezado (logo claro/oscuro, rol activo, selector), selector_rol, pie (sellos), 500
static/img/ · LEEME-identidad.md   paquete de identidad visual
static/src/entrada.css · static/css/app.css   insignia-rol, insignia-autor
locale/en/LC_MESSAGES/   153 cadenas nuevas
README.md · .env.example · requirements.txt · .specify/memory/constitution.md · docs/sdd/constitucion.md · APRENDIZAJE.md
```
