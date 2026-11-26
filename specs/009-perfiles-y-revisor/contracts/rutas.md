# Contrato de rutas: spec 009

Todas las rutas que cambian datos son POST con CSRF. "403" = el rol activo o la relación no alcanza.

## Período actual (admin)
| Ruta | Método | Quién | Respuesta |
| --- | --- | --- | --- |
| `/proyectos/periodos/<pk>/marcar-actual/` | GET | admin | Página de confirmación (dice cuál deja de ser actual) |
| ídem | POST | admin | Marca actual, mensaje y vuelve a la lista |
| ~~`/proyectos/periodos/<pk>/abrir-cerrar/`~~ | — | — | Se elimina |

## Guardados
| Ruta | Método | Quién | Respuesta |
| --- | --- | --- | --- |
| `/comunidad/guardados/` | GET | con sesión | Lista "Guardados" |
| `/comunidad/favoritos/` | GET | — | 301 → `/comunidad/guardados/` |
| `/comunidad/proyecto/<slug>/guardar/` | POST | con sesión | Alterna guardado (la URL `…/favorito/` se mantiene como alias) |

## Plan de estudios (admin)
| Ruta | Método | Respuesta |
| --- | --- | --- |
| `/proyectos/planes/` | GET | Lista de planes con número de asignaturas |
| `/proyectos/planes/nuevo/`, `/proyectos/planes/<pk>/editar/` | GET/POST | Formulario del plan |
| `/proyectos/planes/<pk>/` | GET | Asignaturas del plan por semestre |
| `/proyectos/planes/<pk>/asignaturas/nueva/`, `/proyectos/asignaturas/<pk>/editar/` | GET/POST | Formulario de asignatura |
| `/proyectos/planes/<pk>/activar/`, `/proyectos/asignaturas/<pk>/activar/` | POST | Alterna activo |
| `/proyectos/planes/<pk>/eliminar/`, `/proyectos/asignaturas/<pk>/eliminar/` | POST | Borra si no está en uso; si no, error y ofrece desactivar |

## Perfiles
| Ruta | Método | Quién | Respuesta |
| --- | --- | --- | --- |
| `/personas/<slug>/` | GET | cualquiera | Perfil público; 404 si solo admin o cuenta inactiva |
| `/cuentas/perfil/seccion/<seccion>/` | POST | dueño | Guarda la sección (`foto`, `quitar_foto`, `descripcion`, `aptitudes`, `enlaces`, `asignaturas`) y vuelve al ancla |
| `/cuentas/perfil/experiencia/`, `/cuentas/perfil/estudio/` | POST | dueño | Agrega |
| `/cuentas/perfil/experiencia/<pk>/quitar/`, `/cuentas/perfil/estudio/<pk>/quitar/` | POST | dueño (404 si no es suyo) | Quita |
| `/cuentas/perfil/bienvenida/` | POST | con sesión | `accion=ahora` → edición; `accion=despues` → cierra y no vuelve |
| `/cuentas/disponibilidad/` | POST | rol activo profesor | Alterna "Estoy recibiendo proyectos" |
| `/cuentas/mi-cuenta/` | GET | con sesión | Página con las opciones del menú (sin JS) |

## Revisor elegido
| Ruta | Método | Quién | Respuesta |
| --- | --- | --- | --- |
| `/proyectos/<slug>/enviar/` | GET/POST | autor | Creador: paso "Elige quién revisa" (`profesor` obligatorio salvo reenvío); coautor: envía sin elegir |
| `/proyectos/<slug>/elegir-revisor/` | GET/POST | creador, subestado por_asignar | Elige profesor y crea la solicitud |
| `/proyectos/<slug>/profesores/` | GET | creador | Lista completa (búsqueda `q`, `asignatura`, `semestre`, `disponibles`, `orden`) |
| `/proyectos/<slug>/retirar-solicitud/` | POST | creador, solicitud con ≥ 5 días | Retira y vuelve a elegir |
| `/proyectos/solicitudes/` | GET | rol activo profesor | "Solicitudes de revisión" pendientes |
| `/proyectos/solicitudes/<pk>/aceptar/` | POST | el profesor de la solicitud | En revisión a su nombre |
| `/proyectos/solicitudes/<pk>/no-aceptar/` | GET/POST | el profesor de la solicitud | Mensaje y recomendación opcionales |
| `/proyectos/<slug>/reasignar/` | GET/POST | rol activo admin | Elige nuevo revisor |
| `/proyectos/<slug>/tomar/` | POST | revisor asignado | Enviado (por revisar) → En revisión |

## Plantilla
`{% icono "nombre" %}` · `{% icono "nombre" tam=16 clase="shrink-0" %}` · `{% icono "x" etiqueta="Cerrar" %}`
(con etiqueta: `role="img"` y `aria-label`; sin etiqueta: `aria-hidden="true"`).
