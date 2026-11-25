# Identidad visual — Vitrina de Proyectos UTEQ

Descomprime este paquete en la raíz del repo: las carpetas `static/` y `templates/` caen en su sitio.
`originales/` son los archivos tal como llegaron (no se suben al sitio; sirven de respaldo).

## Qué logo va dónde

| Archivo | Dónde se usa |
|---|---|
| `static/img/logo-uteq.png` / `.webp` | Encabezado en modo claro (lo detecta `config/contexto.py`) y páginas de error |
| `static/img/logo-uteq-blanco.png` / `.webp` | Encabezado en modo oscuro, pie de página verde, imagen para compartir |
| `static/img/marca/sello-carrera-*.png` | Páginas de entrar/registro/activar/recuperar, página pública de verificación, pie de página |
| `static/img/marca/sello-facultad-*.png` | Pie de página (junto al de la carrera) y certificado PDF |
| `static/img/marca/*-pdf.png` | Certificado PDF con reportlab (PNG grandes, reportlab no lee webp) |
| `static/img/marca/uteq-correo.png` | Encabezado de los correos HTML (fondo blanco, URL absoluta) |
| `static/img/favicon.ico` + `static/img/iconos/*` | Favicon (16/32/48), ícono de iPhone, Android/PWA (192, 512, maskable), mosaico de Windows |
| `static/img/iconos/site.webmanifest` | Nombre, colores e íconos al "instalar" el sitio en el celular |
| `static/img/compartir.png` | Vista previa 1200×630 al pegar el enlace en WhatsApp, LinkedIn, Facebook |
| `templates/parciales/iconos.html` | Todas las etiquetas `<link>`/`<meta>` de lo anterior; se incluye en el `<head>` de `base.html` |

## Notas

- El logo UTEQ (verde y blanco) venía con la U recortada en el borde izquierdo; se reconstruyó reflejando su mitad derecha.
  Si consiguen el archivo oficial en SVG, reemplácenlo.
- El favicon usa la Q de UTEQ con la cinta dorada, en blanco sobre el verde #025a27 de la app.
- No deformen ni recoloreen los sellos; dejen un margen libre alrededor de cada logo; tamaño mínimo del sello en pantalla: 48 px.
- El verde del logo oficial es un poco más claro que el #025a27 de la interfaz: es normal, no lo "corrijan".
