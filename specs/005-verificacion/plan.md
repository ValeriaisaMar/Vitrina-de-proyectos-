# Implementation Plan: QR, certificado y verificación

**Branch**: `feature/005-verificacion` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Funciones en `vitrina/verificacion.py` para armar la dirección de verificación, el QR (con
`qrcode`) y el certificado (con `reportlab`); vistas públicas de verificación y de descarga; y
la tarjeta de verificación en el detalle.

## Technical Context

**Dependencies**: `qrcode` y `reportlab` (ya aprobadas y en `requirements.txt`); ninguna nueva.

## Constitution Check

| Principio | Cómo se cumple | Estado |
|---|---|---|
| VI. Integridad | Solo `Proyecto.objects.publicados()`; la página muestra solo los datos permitidos | ✅ |
| III. Entradas | El código se normaliza y se valida con una expresión regular antes de consultar | ✅ |
| XII. Dependencias | Solo qrcode, Pillow y reportlab | ✅ |
| XIII. Configuración | `SITIO_URL` opcional en `.env` y documentada en `.env.example` | ✅ |

## Decisiones de diseño

1. **Generar al momento** (en memoria con `BytesIO`): no hay archivos que sincronizar ni borrar,
   y el contenido siempre coincide con la base de datos.
2. **La dirección del QR** sale de `SITIO_URL` si existe; si no, de la petición.
3. **Rutas por código**: `/verificar/<código>/`, `/verificar/<código>/qr.png` y
   `/verificar/<código>/certificado.pdf`. El código es lo que se comparte.
4. **Certificado en el idioma activo**: se dibuja con `canvas` de reportlab en A4 horizontal.

## Project Structure

```text
vitrina/
├── verificacion.py    normalizar_codigo, url_verificacion, qr_png, certificado_pdf
├── forms.py           + FormularioVerificar
├── views.py           verificar, verificar_codigo, descargar_qr, descargar_certificado
├── urls.py            verificar/, verificar/<codigo>/, .../qr.png, .../certificado.pdf
├── templates/vitrina/ verificar.html, verificado.html, _formulario_verificar.html, detalle.html (tarjeta)
└── tests/             test_verificacion.py; test_paginas.py y test_idioma.py (Verificar ya no es "Próximamente")
proyectos/templates/proyectos/mis_proyectos.html   enlace al certificado
static/fonts/pdf/      archivo-400.ttf, archivo-700.ttf, unbounded-800.ttf
config/settings.py · .env.example   SITIO_URL
static/css/app.css · locale/en/LC_MESSAGES/django.po/.mo · README.md · APRENDIZAJE.md
```
