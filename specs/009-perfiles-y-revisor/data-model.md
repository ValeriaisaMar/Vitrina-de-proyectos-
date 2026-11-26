# Data Model: spec 009

## proyectos

### Periodo (cambia)
| Campo | Tipo | Notas |
| --- | --- | --- |
| es_actual | Boolean, default False | Único cuando es True (restricción condicional) |
| ~~abierto~~ | — | Se elimina tras la migración de datos |

### PlanEstudio (nuevo)
| Campo | Tipo | Notas |
| --- | --- | --- |
| nombre | Char(80), único | "Plan 2022" |
| anio | PositiveSmallInteger | Año del plan |
| activo | Boolean, default True | Varios pueden estar activos |

### Asignatura (cambia)
| Campo | Tipo | Notas |
| --- | --- | --- |
| plan | FK PlanEstudio, PROTECT | Migración: todas a "Plan vigente" |
| codigo | Char(20), blank | Opcional |
| nombre | Char(120) | Deja de ser único global; único con `(plan, nombre)` |

### Proyecto (cambia)
| Campo | Tipo | Notas |
| --- | --- | --- |
| periodo | FK Periodo, PROTECT, **null** | Se asigna al enviar |
| periodo_aprobacion | FK Periodo, PROTECT, null | Se asigna al aprobar; datos: aprobados = periodo |
| imagen_portada | ImageField, blank | webp 1200×675; datos: primera imagen de la galería |
| color_portada | Char(12), choices paleta, default "verde" | Clave, no hex |
| video | URL, blank | http/https |
| demo | (existe) | Se muestra como "Ver proyecto desplegado" |
| revisor | (existe) | Ahora: profesor asignado (aceptó o reasignado) |

Propiedades: `subestado` (`por_asignar`, `esperando`, `por_revisar` o None), `solicitud_pendiente`.

### SolicitudRevision (nuevo)
| Campo | Tipo | Notas |
| --- | --- | --- |
| proyecto | FK Proyecto, CASCADE→PROTECT | `related_name="solicitudes"` |
| profesor | FK Usuario, PROTECT | `related_name="solicitudes_revision"` |
| estado | Char: pendiente, aceptada, no_aceptada, retirada, reasignada | |
| mensaje | Text, blank | Mensaje del profesor al no aceptar |
| profesor_recomendado | FK Usuario, SET_NULL, null | |
| creada_por | FK Usuario, SET_NULL, null | Creador o admin |
| creada_en / respondida_en | DateTime | |
| recordatorio_enviado | Boolean | Recordatorio del día 3 (opcional) |

Restricción: una sola pendiente por proyecto (`UniqueConstraint(fields=["proyecto"], condition=Q(estado="pendiente"))`).
Regla: se puede retirar si `creada_en <= ahora − 5 días`.

### EventoEstado (cambia)
| Campo | Tipo | Notas |
| --- | --- | --- |
| accion | Char: estado, solicitud, aceptada, no_aceptada, retirada, reasignada; default "estado" | Datos existentes = "estado" |

### Transiciones (cambia solo el "quién")
| Desde | Hacia | Quién |
| --- | --- | --- |
| Borrador | Enviado | autor (estudiante); se exige período actual |
| Con observaciones | Enviado | autor; vuelve al mismo revisor |
| Enviado | En revisión | el profesor que es revisor del proyecto (al aceptar o al pulsar "Revisar") |
| En revisión | Aprobado / Con observaciones / Rechazado | el profesor revisor asignado |

## cuentas

### Perfil (nuevo, OneToOne Usuario)
| Campo | Tipo | Notas |
| --- | --- | --- |
| usuario | OneToOne, CASCADE | Se crea con señal `post_save`; migración de datos para existentes |
| slug | Slug(90), único | Estable |
| foto | ImageField, blank | webp 400×400 |
| descripcion | Text(max 600), blank | |
| aptitudes | M2M Aptitud | |
| github / linkedin | URL, blank | Normalizados |
| orcid | Char(19), blank | `0000-0000-0000-000X` validado |
| asignaturas_imparte | M2M proyectos.Asignatura | Solo profesores |
| recibiendo_proyectos | Boolean, default True | |
| bienvenida_vista | Boolean, default False | Existentes activos con sesión previa = True |

### Aptitud (nuevo)
`nombre` Char(50); único sin distinguir mayúsculas (`UniqueConstraint(Lower("nombre"))`).

### ExperienciaLaboral (nuevo)
`perfil` FK, `cargo`, `organizacion`, `inicio` (Date, día 1), `fin` (Date, null = Actualmente),
`descripcion` (Char 300). Validación: fin ≥ inicio.

### Estudio (nuevo)
`perfil` FK, `institucion`, `titulo`, `inicio`, `fin` (null = En curso).

## comunidad

`Favorito` se conserva como modelo (un solo modelo, sin duplicados); cambian textos, `verbose_name`
("guardado") y la URL (`/comunidad/guardados/`, con redirección desde `/comunidad/favoritos/`).
