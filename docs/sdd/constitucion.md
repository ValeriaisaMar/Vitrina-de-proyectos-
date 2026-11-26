# Constitución

La constitución vigente del proyecto está en
[`.specify/memory/constitution.md`](../../.specify/memory/constitution.md).

Ese es el único archivo que se edita. Spec Kit lo lee en cada fase (`specify`, `plan`, `tasks`,
`implement`), así que tenerlo duplicado aquí solo serviría para que las dos copias se
desincronicen.

**Versión vigente:** 3.2.0 (26 de noviembre de 2026): Docker entra al alcance para desplegar y se
aprueban gunicorn y whitenoise.

Versión 3.1.0 (26 de noviembre de 2026): excepción acotada para crear el primer admin
desde la configuración inicial o `createsuperuser` (cuenta activa sin enlace y rol admin sin otro
admin), y el último admin activo no se puede desactivar ni eliminar (spec 010).

Versión anterior: 3.0.0 (25 de noviembre de 2026): el creador elige al profesor revisor, solo el
profesor asignado decide, foto de perfil y portada de hasta 5 MB e íconos SVG locales (spec 009).
