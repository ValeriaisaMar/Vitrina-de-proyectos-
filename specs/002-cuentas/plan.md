# Implementation Plan: Cuentas y autenticación

**Branch**: `feature/002-cuentas` | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

## Summary

Completar la app `cuentas`: registro con activación por correo, inicio de sesión con límite de
intentos, recuperación de contraseña, perfil, cambio de contraseña y el decorador
`@rol_requerido` con su página 403. Se apoya en las vistas y formularios de autenticación de
Django y agrega solo lo que falta.

## Technical Context

**Language/Version**: Python 3.12+ · **Primary Dependencies**: Django 6.1.3 (sin dependencias nuevas)

**Storage**: PostgreSQL (sin migraciones nuevas) y caché de Django para los intentos fallidos

**Testing**: `django.test.TestCase`, `mail.outbox`, `override_settings`

**Constraints**: enlaces de un solo uso y 24 h; respuestas que no revelan cuentas; todo en español e inglés

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| III. Entradas no confiables | Formularios con CSRF; `next` validado con `url_has_allowed_host_and_scheme` | ✅ |
| IV. Autenticación segura | Activación obligatoria, tokens de Django de 24 h, recuperación neutra, validadores, bloqueo 5/15 min | ✅ |
| V. Permisos por rol | `@rol_requerido` verifica en el servidor; 403 con diseño | ✅ |
| VIII. Pruebas | Un caso por escenario de aceptación | ✅ |
| IX. Código entendible | Vistas basadas en funciones; las de recuperación y cambio de contraseña reutilizan las de Django | ✅ |
| XI. Idioma | Plantillas, formularios y correos traducibles | ✅ |
| XII. Dependencias | Ninguna nueva | ✅ |

## Decisiones de diseño

1. **Token de activación propio** (`cuentas/tokens.py`): hereda de
   `PasswordResetTokenGenerator` y suma `is_active` al hash. Así el enlace deja de servir en
   cuanto la cuenta se activa (un solo uso) sin guardar nada en la base de datos. Vence con
   `PASSWORD_RESET_TIMEOUT` (24 h).
2. **Envío de correos en `cuentas/correos.py`**: una función `enviar_activacion()` arma el correo
   en texto y HTML con plantillas. Si el servidor de correo falla, se registra y la vista avisa
   sin perder la cuenta creada.
3. **Límite de intentos en `cuentas/limite.py`**: tres funciones (`esta_bloqueado`,
   `registrar_fallo`, `limpiar`) sobre la caché de Django, con clave `login:<correo>:<ip>`.
4. **Formulario de inicio de sesión** (`FormularioEntrar`): hereda de `AuthenticationForm`,
   cambia la etiqueta a "Correo electrónico", agrega "Mantener la sesión iniciada" y detecta la
   cuenta inactiva con contraseña correcta para mostrar el mensaje de activación.
5. **Vistas basadas en funciones** para registro, activación, reenvío, entrar, perfil y 403.
   Para recuperar y cambiar la contraseña se usan las vistas de clase de Django con nuestras
   plantillas, porque ya resuelven tokens y validaciones de forma segura.
6. **URLs con espacio de nombres** `cuentas:` y rutas en español. `LOGIN_URL` pasa a
   `cuentas:entrar` y se quita el `include("django.contrib.auth.urls")` temporal del 001.
7. **Diseño**: las pantallas de entrar y registrarse usan dos columnas (panel verde con el
   mensaje de la marca + formulario), como en el lienzo de diseño; perfil y recuperación usan
   una tarjeta sobria.

## Project Structure

```text
specs/002-cuentas/ spec.md · plan.md · tasks.md
cuentas/
├── tokens.py            NUEVO: generador del token de activación
├── correos.py           NUEVO: envío del correo de activación
├── limite.py            NUEVO: bloqueo por intentos fallidos
├── decoradores.py       NUEVO: @rol_requerido
├── forms.py             + FormularioRegistro, FormularioEntrar, FormularioReenvio, FormularioPerfil
├── views.py             NUEVO: registro, activar, reenviar, entrar, salir, perfil, 403
├── urls.py              NUEVO: app_name = "cuentas"
├── templates/cuentas/   entrar, registro, revisa_correo, activacion_invalida, reenviar,
│                        perfil, contrasena_*.html, _panel_marca.html
├── templates/cuentas/correos/ activacion_asunto.txt, activacion.txt, activacion.html,
│                        recuperacion_asunto.txt, recuperacion.txt, recuperacion.html
└── tests/               test_registro, test_entrar, test_recuperacion, test_perfil, test_permisos
config/settings.py       LOGIN_URL, CACHES
config/urls.py           include("cuentas.urls"), handler403
templates/403.html       NUEVO
templates/parciales/encabezado.html, pie.html      enlaces nuevos
vitrina/templates/vitrina/inicio.html               enlaces nuevos
locale/en/LC_MESSAGES/django.po, django.mo         textos nuevos
```

**Se elimina**: `templates/registration/login.html` (pasa a `cuentas/templates/cuentas/entrar.html`).
