# Contrato: página `/configuracion-inicial/` (nombre de URL `configuracion_inicial`)

| Situación | GET | POST |
|---|---|---|
| Hay admin activo | 404 | 404 |
| Sin admin, con sesión iniciada | 200, aviso "cierra sesión" con botón Salir | igual que GET (no procesa) |
| Sin admin, visitante | 200, asistente; si no hay código vigente, genera uno y lo escribe en el log | procesa |
| IP bloqueada (5 fallos / 15 min) | 200 | 200 con aviso de bloqueo, no procesa |

## GET

- `?opcion=nueva` (por defecto) o `?opcion=existente` elige la pestaña.
- El HTML nunca contiene el código.

## POST (CSRF)

Campo oculto `opcion`:

- `nueva`: `codigo`, `nombres`, `apellidos`, `email`, `password1`, `password2`.
- `existente`: `codigo`, `email`, `password`.

Resultados:

- **Éxito**: inicia sesión (rol activo admin), `messages.success("Listo. Ya eres administrador de la Vitrina.")`,
  302 → `vitrina:panel`, que muestra los siguientes pasos una vez.
- **Código malo / cuenta incorrecta**: 200, error genérico "El código o los datos de la cuenta no son
  válidos. Revisa e inténtalo de nuevo." (mismo texto en ambos casos).
- **Correo ya registrado (pestaña nueva, código correcto)**: 200, error en el campo correo invitando a
  usar la pestaña de cuenta existente.
- **Contraseña débil / no coincide**: 200, errores de los validadores de Django.
- **Otro envío ganó la carrera**: 404.

## Enlace en Entrar

`cuentas:entrar` recibe `mostrar_configuracion_inicial` (bool, de la caché). Si es True, al final:
línea fina, ícono `settings`, texto pequeño `text-texto-suave`:
"¿Instalación nueva? Configurar la administración" → `{% url 'configuracion_inicial' %}`.
