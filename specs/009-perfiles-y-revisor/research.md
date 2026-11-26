# Research: spec 009

## 1. Subestados de "Enviado" en lugar de estados nuevos

- **Decision**: no se agregan valores a `Estado`. Un proyecto Enviado está en uno de tres subestados,
  calculados por `Proyecto.subestado`:
  - `por_asignar`: sin revisor y sin solicitud pendiente ("Por asignar revisor").
  - `esperando`: con una `SolicitudRevision` pendiente ("Esperando aceptación").
  - `por_revisar`: con revisor ya asignado (reenvío tras observaciones o reasignación del admin).
- **Rationale**: la constitución y todo el código (filtros, insignias, paneles, pruebas) ya conocen
  los seis estados. Los subestados no cambian quién puede editar ni qué es público. La tabla
  `TRANSICIONES` solo cambia el "quién" de Enviado → En revisión: el profesor que es `revisor` del
  proyecto. Aceptar una solicitud = asignar `revisor` + `cambiar_estado(EN_REVISION)` en una transacción.
- **Alternatives considered**: estados `por_asignar` y `esperando_aceptacion` (obliga a migrar todos
  los filtros y la constitución, y duplica lógica que ya vive en `SolicitudRevision`).

## 2. Historial del flujo de solicitudes

- **Decision**: `EventoEstado.accion` con default `estado`. Las acciones de solicitud se guardan como
  eventos con `estado_anterior == estado_nuevo` (salvo aceptar, que además cambia el estado).
- **Rationale**: una sola línea de tiempo, inmutable, que ya se muestra en el detalle y la revisión.
- **Alternatives considered**: mostrar las `SolicitudRevision` mezcladas con los eventos (dos fuentes
  que ordenar en cada plantilla).

## 3. ¿Quién envía y quién elige?

- **Decision**: cualquier autor envía; si es el creador, en el mismo paso elige profesor. Si envía un
  coautor, queda `por_asignar` y el creador ve un aviso. Reenvío con observaciones: vuelve al mismo
  revisor (`por_revisar`), sin elegir.
- **Rationale**: respeta "solo el creador elige" sin quitarles a los coautores el envío que ya tienen.

## 4. Algoritmo de sugerencias

- **Decision**: `sugerir_profesores(proyecto, limite=5)` en `proyectos/solicitudes.py`, en Python
  sobre datos agregados con pocas consultas:
  - +3 imparte la asignatura del proyecto (`Perfil.asignaturas_imparte`).
  - +2 por cada proyecto aprobado de esa asignatura que revisó, con tope de 3 proyectos (máx. +6).
  - +1 si revisó proyectos del mismo semestre (otras asignaturas).
  - +1 por cada aptitud que coincida (sin mayúsculas) con una tecnología del proyecto.
  - Desempate: menos pendientes (solicitudes pendientes + proyectos En revisión/por revisar), luego nombre.
  - Excluye autores, no disponibles, cuentas inactivas, sin rol profesor y quienes no aceptaron este proyecto.
  - Solo se sugieren profesores con puntaje > 0; cada uno lleva su lista de motivos traducibles.
- **Rationale**: transparente y comprobable en pruebas; los datos son pequeños.

## 5. Íconos

- **Decision**: SVG copiados a `static/iconos/` desde `@tabler/icons` (MIT, trazo) y `simple-icons`
  (CC0; LinkedIn se toma de la versión 9.x, la última que lo incluye). Licencias en
  `static/iconos/LICENCIAS.txt`. `{% icono "nombre" tam=20 clase="" etiqueta="" %}` inserta el SVG
  en línea con `aria-hidden="true"`, o con `role="img"` y `aria-label` si se pasa `etiqueta`.
- **Rationale**: en línea hereda `currentColor` (modo oscuro gratis) y no hace peticiones extra.
- **Alternatives considered**: sprite `<use>` (más complejo de mantener a mano), CDN (prohibido).

## 6. Imágenes subidas

- **Decision**: `config/imagenes.py`: tamaño ≤ 5 MB, extensión jpg/jpeg/png/webp, `Image.open` +
  `verify()` y reabrir, formato real en {JPEG, PNG, WEBP}, límite de píxeles (Pillow ya protege con
  `MAX_IMAGE_PIXELS`), `ImageOps.exif_transpose`, recorte centrado (`ImageOps.fit`) a 1200×675
  (portada) o 400×400 (foto), webp calidad 85, nombre `uuid4().hex + ".webp"`.
- **Rationale**: reprocesar elimina metadatos (EXIF con GPS) y cualquier contenido extra del archivo.

## 7. Tofu en la portada de color

- **Hallazgo**: la portada de color es CSS (inicial del título en Unbounded). Las fuentes del sitio
  y del PDF sí tienen tildes, ñ, ü, ¿, ¡, «» y comillas tipográficas (revisado con fontTools fuera del
  proyecto). Lo que no tienen: algunos signos (por ejemplo `→`) y no todas combinan bien marcas
  sueltas. Un título pegado desde macOS o un PDF llega en **NFD** (letra + tilde combinante): la
  portada toma solo el primer *code point* y en el certificado reportlab dibuja la marca suelta (sin
  composición), que se ve como caja o mal puesta.
- **Decision**: normalizar a NFC al guardar (formularios de proyecto, comentarios, perfil y registro)
  y una migración de datos que normaliza lo existente; la inicial de la portada toma el primer
  grafema; el PDF normaliza antes de dibujar y reemplaza los caracteres sin glifo por uno parecido.
  Las pruebas revisan los glifos con `reportlab.pdfbase.ttfonts.TTFontFile` (dependencia aprobada).

## 8. Período actual

- **Decision**: `Periodo.es_actual` + `UniqueConstraint(fields=["es_actual"], condition=Q(es_actual=True))`.
  `marcar_actual(periodo)` en una transacción desmarca y marca. Caché `periodo_actual` (clave fija,
  invalidada en `save`/`delete`). Confirmación con página GET → POST (funciona sin JS).
- **Migración**: 1) agrega `es_actual`; 2) datos: el abierto más reciente por `fecha_inicio` queda
  actual (reversa: los actuales vuelven a abiertos); 3) quita `abierto` (reversa la vuelve a crear).

## 9. Perfil público

- **Decision**: `Perfil.slug` = `slugify(nombres apellidos)` + sufijo numérico si se repite, generado
  una vez y nunca recalculado. Visible si el usuario está activo y tiene rol estudiante o profesor.
  Edición en la misma página: cada sección tiene un `<details>` con su formulario (POST + redirección
  al ancla), así funciona sin JS. Aptitudes con `<datalist>` y texto separado por comas.
- **Personas relacionadas**: tres consultas con `values(...).annotate(Count("proyecto", distinct=True))`
  (coautores, revisores, revisados) y una para traer los perfiles; se combinan en Python.

## 10. Menú de la cuenta

- **Decision**: el avatar es un `<a href="{% url 'cuentas:mi_cuenta' %}">` con `aria-haspopup`;
  `menu.js` lo convierte en botón (`aria-expanded`), abre el panel, enfoca el primer ítem, cierra con
  `Esc`/clic fuera y devuelve el foco. En celular el panel es `fixed inset-x-0` a todo el ancho.
  Contadores (solicitudes pendientes y bandeja) en el procesador de contexto, solo si el rol activo
  es profesor: una consulta por contador.
