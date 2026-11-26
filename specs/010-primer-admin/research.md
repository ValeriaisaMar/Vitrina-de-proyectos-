# Research: Configuración inicial (spec 010)

## R1. Cómo guardar el código

- **Decision**: SHA-256 del código normalizado (sin guiones ni espacios, en mayúsculas), comparado con
  `hmac.compare_digest`. Solo se guarda el hash.
- **Rationale**: 12 caracteres de 31 símbolos ≈ 59 bits de azar y vence en 30 minutos, con 5 intentos
  por código: un hash rápido basta y es fácil de explicar. `compare_digest` evita filtrar por tiempo.
- **Alternatives**: `make_password` (más lento y en pruebas usa MD5; innecesario con tanta entropía);
  guardar el código cifrado (habría que manejar una clave; no aporta nada).

## R2. Alfabeto y formato

- **Decision**: `23456789ABCDEFGHJKMNPQRSTUVWXYZ` (31 símbolos: sin 0, O, 1, I, L), `secrets.choice`,
  mostrado `XXXX-XXXX-XXXX`.

## R3. Registro único y concurrencia

- **Decision**: modelo `ConfiguracionInicial` con `pk=1` (`obtener()` hace `get_or_create(pk=1)`).
  `crear_primer_admin` abre `transaction.atomic()`, toma `select_for_update()` de esa fila y vuelve a
  comprobar `hay_admin_activo()` dentro. El segundo envío espera el bloqueo y al entrar ve que ya hay
  admin → `ConfiguracionNoDisponible`.
- **Fallos dentro de la transacción**: un error lanzado dentro de `atomic` deshace también el aumento
  de `intentos_fallidos`. Por eso el servicio anota el fallo, deja que la transacción termine bien y
  lanza la excepción después.
- **Alternatives**: restricción única en la base (no hay una columna natural "es el primer admin");
  bloquear la tabla de usuarios (excesivo).

## R4. Caché del indicador del enlace

- **Decision**: `cache.get_or_set("configuracion_inicial:hay_admin", hay_admin_activo, 60)`. Se borra
  con señales `post_save`/`post_delete` de `Usuario` y `RolAsignado` y al terminar la configuración.
- **Rationale**: `LocMemCache` es por proceso; con varios procesos de gunicorn, borrar en uno no borra
  en los otros. El vencimiento de 60 s acota el desfase y la página y el servicio nunca usan la caché,
  así que un enlace de más solo lleva a un 404.
- **Note**: `QuerySet.update()` no dispara señales; la app no lo usa sobre `is_active`. El vencimiento
  cubre ese caso y los cambios hechos directamente en la base.

## R5. Logging en producción

- **Decision**: `LOGGING` explícito con `disable_existing_loggers: False`, handler `consola`
  (`StreamHandler`, stderr, sin filtro de DEBUG) y formatter `{asctime} {levelname} {name}: {message}`.
  Logger `cuentas` (INFO, `propagate: False`) y `django` (nivel `NIVEL_LOG_DJANGO`, por defecto INFO,
  `propagate: False`). `django.server` queda con su configuración propia (Django la redefine al
  fusionar). No hay `ADMINS` configurado, así que no hay envío de errores por correo que preservar;
  se deja `mail_admins` fuera para no cambiar ese comportamiento.
- **Rationale**: con `DEBUG=False`, el handler `console` de Django filtra con `require_debug_true` y
  los WARNING del proyecto solo llegan al "último recurso" de Python. Docker/systemd guardan solo
  stdout/stderr.

## R6. Límite de intentos

- **Decision**: reutilizar `cuentas/limite.py` con la clave `configuracion-inicial` y la IP:
  cada envío fallido (código o cuenta) suma; a los 5 se bloquea 15 minutos. Aparte, el registro cuenta
  `intentos_fallidos` del código vigente y lo borra a los 5 (WARNING en el log).

## R7. Cuenta existente y tiempos

- **Decision**: buscar por correo sin distinguir mayúsculas y `check_password`; si no existe se llama
  `Usuario().set_password(...)` para gastar el mismo tiempo (como hace `ModelBackend`). No se usa
  `authenticate` porque rechaza cuentas inactivas, y una cuenta nunca activada puede promoverse.

## R8. Rol y registro de cambios

- **Decision**: campo nuevo `CambioRol.motivo` (CharField, blank). `asignar_roles`/`dar_rol` aceptan
  `motivo=""`. Cuenta nueva: `create_user(roles=[ADMIN], is_active=True)` + `CambioRol` "agregado" con
  `hecho_por=None` y motivo. Cuenta existente: `dar_rol(usuario, ADMIN, actor=None, motivo=…)`.
  `create_superuser` deja también su `CambioRol` con el mismo motivo e invalida código y caché.
- **is_staff**: el primer admin web **no** recibe `is_staff`/`is_superuser`. El panel de Django es
  para cuentas técnicas y la gestión de usuarios de la app no edita superusuarios; un admin web
  superusuario no podría ser gestionado por otros admins.

## R9. Siguientes pasos en el panel

- **Decision**: al terminar, la vista guarda `request.session["primeros_pasos"] = True`; la vista del
  panel del admin la saca con `pop` y muestra una tarjeta con tres enlaces (correo de envío, períodos,
  planes). El mensaje "Listo…" va con `messages.success`.

## R10. Pestañas sin JavaScript

- **Decision**: dos enlaces con aspecto de pestañas (`?opcion=nueva` / `?opcion=existente`,
  `aria-current`) y un campo oculto `opcion` en el POST. Funciona sin JS y con teclado.

## R11. Último admin en el panel de Django

- **Decision**: `UsuarioCambioForm.clean` rechaza desactivar al último admin; `has_delete_permission`
  devuelve False para él; la acción masiva "borrar seleccionados" se envuelve y se niega si dejaría
  la plataforma sin admin activo; el formset de la tabla de roles rechaza quitar la fila admin del
  último admin. En la app, `FormularioGestionUsuario` también valida desactivar al último admin.
