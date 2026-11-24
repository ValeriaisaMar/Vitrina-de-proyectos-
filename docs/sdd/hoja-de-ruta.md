# Hoja de ruta

Entrega: **jueves 26 de noviembre de 2026**. Presentación: viernes 27.

## Módulos

| # | Módulo | Rama | Día | Commit lo hace (propuesta) |
|---|---|---|---|---|
| 001 | Base de la plataforma | `feature/001-base-plataforma` | Martes | Abelardo |
| 002 | Cuentas y autenticación | `feature/002-cuentas` | Martes | Valeria |
| 003 | Proyectos, explorar y detalle | `feature/003-proyectos` | Martes | Dayana |
| 004 | Revisión e historial | `feature/004-revision` | Miércoles | Abelardo |
| 005 | QR, certificado y verificación | `feature/005-verificacion` | Miércoles | Valeria |
| 006 | Paneles por rol | `feature/006-paneles` | Miércoles | Dayana |
| 007 | Comunidad | `feature/007-comunidad` | Jueves | Abelardo |
| — | Pulido, datos de demostración y ensayo | `feature/008-pulido` | Jueves | Todos |

Comunidad es el único módulo que puede quedar fuera si falta tiempo (constitución, principio XV).

## Ciclo de cada módulo

1. **Spec**: se escribe `specs/NNN-modulo/spec.md` y el equipo la revisa.
2. **Plan**: con la spec aprobada se escribe `plan.md` (modelos, vistas, URLs, plantillas, pruebas).
3. **Tareas**: `tasks.md` con pasos pequeños y en orden.
4. **Implementación**: se programa y se prueba con `python manage.py test`, y cada tarea se
   anota en `APRENDIZAJE.md`.
5. **Entrega**: se recibe un `.zip` con los archivos del módulo y el mensaje de commit sugerido.
   Quien tiene el turno crea la rama, copia los archivos, hace commit y push, y abre el Pull
   Request.
6. **Integración**: otro integrante revisa el Pull Request y lo integra a `main`.

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Alcance | Solo la carrera de Ingeniería de Software, Facultad de Ciencias de la Computación |
| Fuera de alcance | Health Score, Cementerio y Resurrección, Árbol genealógico y Docker |
| Roles | Visitante, estudiante, profesor y admin; el admin asigna roles |
| Revisión | Bandeja común: cualquier profesor puede tomar un proyecto |
| Autores | Uno o varios, todos con cuenta; cualquiera de ellos puede editar |
| Datos académicos | El proyecto guarda la asignatura y el periodo |
| Cuentas | Cualquier correo real, verificado con un enlace de activación |
| Correo de envío | `vitrinadeproyectosuteq@gmail.com` (provisional, falta definir el de producción) |
| Verificación | Código `VP-AAAA-NNNN`, QR en PNG y certificado en PDF |
| Comunidad | Me gusta, favoritos y comentarios; los ocultan el autor y el admin |
| Diseño | Neo-brutalismo institucional; verde `#025a27` protagonista y amarillo `#ecb932` de acento |
| Tipografía | Unbounded (títulos) y Archivo (texto) |
| Frontend | Plantillas de Django y Tailwind con el ejecutable standalone |
| Idiomas | Español por defecto e inglés |
| Tema | Claro y oscuro, por defecto según el sistema |
| Código | Cuatro apps: `cuentas`, `proyectos`, `comunidad` y `vitrina` |
