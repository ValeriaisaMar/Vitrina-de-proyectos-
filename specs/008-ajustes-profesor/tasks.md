# Tasks: Ajustes pedidos por el profesor

**Input**: [spec.md](spec.md) y [plan.md](plan.md). Cada historia deja su entrada en `APRENDIZAJE.md`.

## Preparación

- [x] T000 Rama `feature/008-ajustes-profesor`, suite en verde antes de empezar (277 pruebas, con
  "salir del proyecto" y "transferir" que estaban pendientes), aprobación de `cryptography`

## Historia 1 (P1) — Varios roles

- [x] T101 `RolAsignado`, `CambioRol`, `Usuario.ultimo_rol`; migraciones 0002 (esquema), 0003 (datos), 0004 (quitar `rol`)
- [x] T102 Servicio `cuentas/roles.py` (al menos un rol, último admin, registro); manager y `createsuperuser`
- [x] T103 `RolActivoMiddleware`, procesador de contexto `roles`, `rol_requerido` con rol activo
- [x] T104 Revisar los usos de `.rol`, `es_*` y `rol_requerido` (rol activo vs. tiene el rol); conflicto de interés
- [x] T105 Selector "Entrar como", rol activo en el encabezado, casillas en la gestión, filtro y etiquetas, "Mis roles"
- [x] T106 Pruebas: migración de datos, selector, permisos por rol activo, sesión manipulada, último admin, conflicto, rol quitado

## Historia 2 (P2) — Periodos

- [x] T201 Modelo `Periodo`; migraciones 0005 (campo nuevo), 0006 (datos), 0007 (quitar texto y renombrar)
- [x] T202 Formulario del proyecto con periodos abiertos; filtros de Explorar por slug; panel y certificado con el nombre
- [x] T203 Sección "Periodos" del admin: lista, crear, editar, abrir/cerrar, borrar solo sin proyectos
- [x] T204 Pruebas de gestión, formulario, vitrina y migración de datos

## Historia 3 (P3) — Correo de envío

- [x] T301 `ConfiguracionCorreo` (singleton) y cifrado Fernet con `CLAVE_CIFRADO`
- [x] T302 `CorreoConfigurableBackend` en `MAILERS` con respaldo del `.env`
- [x] T303 Página "Correo de envío": configuración rápida, probar sin guardar con límite, tarjeta de estado
- [x] T304 Pruebas sin SMTP real: cifrado, permiso, contraseña vacía, errores, respaldo

## Historia 4 (P4) — Comentarios

- [x] T401 `Comentario.respuesta_a`, validación de un nivel, `puede_responder`, vista `responder`
- [x] T402 Plantilla con autor destacado, "Docente revisor", hilo con sangría y formulario en línea; correo al responder
- [x] T403 Pruebas: etiqueta, solo autores, sin segundo nivel, ocultar el hilo, sin N+1

## Historia 5 (P5) — Identidad visual

- [x] T501 `iconos.html` en `base.html`; logo claro/oscuro con `<picture>`; sellos en pie, cuentas y verificación
- [x] T502 Logo y sellos en el certificado PDF; logo en correos HTML y en la página 500; Open Graph del detalle
- [x] T503 Pruebas de identidad visual

## Cierre

- [x] T900 Traducciones, Tailwind, README, `.env.example`, constitución 2.1.0, `APRENDIZAJE.md`, suite completa
