"""Ayudas compartidas por las pruebas de proyectos y de la vitrina."""

import datetime
import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image as PilImage

from proyectos.models import Asignatura, Autoria, Estado, Periodo, Proyecto, Tecnologia

PDF_MINIMO = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def imagen_png(nombre="captura.png", tamano=(40, 30)):
    """Una imagen PNG real y pequeña, creada en memoria."""
    buffer = io.BytesIO()
    PilImage.new("RGB", tamano, (2, 90, 39)).save(buffer, "PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


def pdf(nombre="informe.pdf", contenido=PDF_MINIMO):
    return SimpleUploadedFile(nombre, contenido, content_type="application/pdf")


def periodo(nombre="2026-2", abierto=True, **extra):
    """Devuelve el Periodo con ese nombre; si no existe, lo crea (fecha de inicio según -1/-2)."""
    try:
        anio, semestre = nombre.split("-")
        inicio = datetime.date(int(anio), 7 if semestre == "2" else 1, 1)
    except ValueError:
        inicio = datetime.date(2026, 11, 1)
    datos = {"fecha_inicio": inicio, "abierto": abierto, **extra}
    return Periodo.objects.get_or_create(nombre=nombre, defaults=datos)[0]


def crear_proyecto(creador, titulo="Gestor de tutorías", estado=Estado.BORRADOR, coautores=(), tecnologias=("Django",), **extra):
    """Crea un proyecto directamente en la base de datos (sin pasar por el formulario)."""
    datos = {
        "titulo": titulo,
        "resumen": "Una aplicación para organizar tutorías entre estudiantes.",
        "descripcion": "Descripción larga del proyecto.\n\nSegundo párrafo.",
        "asignatura": Asignatura.objects.order_by("semestre", "nombre").first(),
        "periodo": "2026-2",  # texto por comodidad: abajo se convierte en Periodo
        "repositorio": "https://github.com/uteq/gestor",
        "estado": estado,
    }
    datos.update(extra)
    if isinstance(datos["periodo"], str):
        datos["periodo"] = periodo(datos["periodo"])
    proyecto = Proyecto.objects.create(**datos)
    Autoria.objects.create(proyecto=proyecto, usuario=creador, es_creador=True)
    for usuario in coautores:
        Autoria.objects.create(proyecto=proyecto, usuario=usuario)
    proyecto.tecnologias.set(Tecnologia.objects.filter(nombre__in=tecnologias))
    return proyecto


class MediaTemporal:
    """Mezcla para pruebas: los archivos subidos van a una carpeta temporal que se borra al final."""

    @classmethod
    def setUpClass(cls):
        cls._media = tempfile.mkdtemp(prefix="vitrina-pruebas-")
        cls._ajuste = override_settings(MEDIA_ROOT=cls._media)
        cls._ajuste.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._ajuste.disable()
        shutil.rmtree(cls._media, ignore_errors=True)
