<!--
Sync Impact Report
Version change: sin versión adoptada (plantilla) → 1.0.0
Principios añadidos: los 14 principios de Tecnología, Consultas seguras,
  Entradas no confiables, Permisos por rol, Integridad de la verificación,
  Health Score, Conservación de datos, Pruebas, Plantillas y estilos,
  Dependencias, Secretos y configuración, Idioma, Flujo de trabajo y
  Prioridad del núcleo.
Secciones añadidas: Restricciones operativas para la IA; Revisión de cumplimiento.
Secciones eliminadas: ninguna.
Pendientes: TODO(RATIFICATION_DATE): confirmar la fecha original de adopción.
-->
# Constitución de Vitrina de Proyectos

## Core Principles

### I. Tecnología
Todo el código MUST usar Python 3.12 o superior y Django 6.1, dentro del proyecto
`config` y la aplicación `vitrina`. La base de datos MUST ser PostgreSQL y el
despliegue MUST usar Docker. Estas tecnologías no se cambian sin aprobación
expresa, para mantener una plataforma coherente y soportable.

### II. Consultas seguras
Las consultas a la base de datos MUST usar el ORM de Django. MUST NOT escribirse
SQL manual ni construirse consultas mediante f-strings; así se conserva el acceso
tipado del ORM y se evita interpolar datos en consultas.

### III. Entradas no confiables
Todo texto recibido de usuarios, incluidos formularios, parámetros de URL,
enlaces a repositorios y comentarios, MUST tratarse como no confiable y mostrarse
con el escapado automático de las plantillas. Los enlaces externos MUST validarse
antes de guardarse para reducir el riesgo de contenido engañoso o inseguro.

### IV. Permisos por rol
Cada vista MUST verificar en el servidor el rol del usuario: visitante,
estudiante, docente/revisor o administrador. Un estudiante MUST editar únicamente
sus propios proyectos y solo mientras no estén verificados. Ocultar controles en
la plantilla MUST NOT considerarse un control de acceso.

### V. Integridad de la verificación
La vitrina pública MUST mostrar únicamente proyectos verificados. Un proyecto
MUST NOT verificarse sin una decisión explícita de un docente o revisor; la
publicación pública depende de esa revisión humana.

### VI. El Health Score apoya, no decide
El Health Score MUST estar entre 0 y 100 y servir únicamente como apoyo al
revisor. MUST NOT verificar ni rechazar un proyecto de forma automática, para
mantener la decisión de revisión bajo responsabilidad humana.

### VII. Conservación de datos
Los proyectos enviados al Cementerio MUST conservar su historial, observaciones
y genealogía. Los cambios de estado MUST NOT eliminar datos; la conservación
permite auditar la evolución y posibilita la resurrección de proyectos.

### VIII. Pruebas
Toda funcionalidad nueva MUST incluir pruebas automáticas en `vitrina/tests.py`
o en el paquete `vitrina/tests/`. La suite completa, ejecutada con
`python manage.py test`, MUST pasar antes de integrar cambios.

### IX. Plantillas y estilos
Las plantillas MUST heredar de `vitrina/templates/vitrina/base.html`. Los estilos
MUST ubicarse en `vitrina/static/vitrina/css/style.css`, para mantener una
presentación consistente y centralizada.

### X. Dependencias
No se MUST agregar paquetes a `requirements.txt` sin aprobación expresa, para
evitar incorporar dependencias, mantenimiento y riesgos no evaluados.

### XI. Secretos y configuración
Las credenciales y claves MUST residir en `.env`, que MUST NOT subirse al
repositorio. `.env.example` MUST mantenerse actualizado y sin valores reales. En
producción, `DEBUG` MUST ser `False`.

### XII. Idioma
Los textos de interfaz, mensajes y documentación MUST estar en español. Los
nombres de código MAY estar en español o inglés, pero MUST mantener un uso
consistente dentro del proyecto.

### XIII. Flujo de trabajo
La rama `main` MUST mantenerse estable. Cada funcionalidad MUST desarrollarse
en su propia rama `feature/...` e integrarse mediante Pull Request. Los commits
MUST seguir los prefijos `feat:`, `fix:`, `docs:` o `test:`.

### XIV. Prioridad del núcleo
El núcleo —publicación, revisión docente y vitrina pública— MUST completarse y
pasar sus pruebas antes de construir complementos. Health Score, Cementerio y
Resurrección, árbol genealógico y comunidad MUST quedar subordinados a ese orden.

## Restricciones operativas para la IA

- La IA MUST modificar únicamente los archivos enumerados en el plan de cada
  funcionalidad.
- La IA MUST NOT borrar ni modificar migraciones existentes; los cambios de
  modelos MUST realizarse mediante migraciones nuevas.
- La IA MUST NOT ejecutar comandos fuera de la carpeta del proyecto.
- La IA MUST NOT leer, mostrar ni modificar `.env`.
- La IA MUST NOT ejecutar comandos destructivos sobre la base de datos, incluidos
  `flush` o el borrado de tablas, sin confirmación expresa.

## Revisión de cumplimiento

Cada Pull Request MUST comprobar el cumplimiento de los principios aplicables,
la inclusión de pruebas para la funcionalidad nueva y el resultado satisfactorio
de `python manage.py test`. Las desviaciones requieren aprobación expresa y
documentación en el Pull Request antes de integrar.

## Governance

Las enmiendas a esta constitución MUST proponerse mediante Pull Request e incluir
la justificación, el impacto sobre principios y prácticas existentes, y la
actualización de versión y fecha. La integración requiere aprobación expresa.

El versionado MUST seguir SemVer: MAJOR para retirar o cambiar de forma
incompatible una regla; MINOR para agregar principios o ampliar materialmente
las reglas; PATCH para aclaraciones y correcciones sin cambio de significado.

Quienes revisen Pull Requests MUST verificar su conformidad con esta constitución
y dejar documentadas las excepciones aprobadas. En caso de conflicto, esta
constitución prevalece sobre prácticas locales incompatibles hasta que se apruebe
una enmienda.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): confirmar la fecha original de adopción | **Last Amended**: 2026-11-22
