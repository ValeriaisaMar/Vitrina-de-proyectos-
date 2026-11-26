"""Spec 009, historia 2b: tildes, ñ, ü, ¿, ¡ y comillas tipográficas sin "cajitas".

Los glifos se revisan con el lector de fuentes TTF de reportlab (dependencia aprobada). Las fuentes
web (woff2) son las mismas familias; se revisaron con fontTools fuera del proyecto.
"""

import io
import unicodedata
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from reportlab.pdfbase.ttfonts import TTFontFile

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from config.texto import nfc, para_pdf
from proyectos.models import Estado, Proyecto
from proyectos.tests.utilidades import MediaTemporal, crear_proyecto, imagen_png

TITULO = "Diseño de ñandúes: Árbol, pingüino y «más» ¿sí?"
EXTRA = "¡Hola! “comillas” ‘simples’ ÜÑÁÉÍÓÚ"
FUENTES_PDF = Path(settings.BASE_DIR) / "static" / "fonts" / "pdf"


class GlifosDeLasFuentesTests(TestCase):
    def test_las_fuentes_del_pdf_tienen_todos_los_caracteres(self):
        usados = {c for c in TITULO + EXTRA if not c.isspace()}
        for archivo in sorted(FUENTES_PDF.glob("*.ttf")):
            glifos = TTFontFile(str(archivo)).charToGlyph
            faltan = sorted(c for c in usados if ord(c) not in glifos)
            self.assertEqual(faltan, [], f"A {archivo.name} le faltan: {faltan}")


class NormalizacionTests(TestCase):
    def test_nfc_compone_las_letras(self):
        descompuesto = unicodedata.normalize("NFD", TITULO)
        self.assertNotEqual(descompuesto, TITULO)
        self.assertEqual(nfc(descompuesto), TITULO)

    def test_para_pdf_cambia_lo_que_la_fuente_no_trae(self):
        glifos = TTFontFile(str(FUENTES_PDF / "archivo-400.ttf")).charToGlyph
        tiene = lambda c: ord(c) in glifos  # noqa: E731
        self.assertEqual(para_pdf(unicodedata.normalize("NFD", TITULO), tiene), TITULO)
        self.assertEqual(para_pdf("A → B", tiene), "A -> B")
        self.assertTrue(all(tiene(c) for c in para_pdf("ﬁn ẞ 🚀", tiene) if not c.isspace()))

    def test_el_formulario_guarda_en_nfc(self):
        ana = crear_usuario("ana@correo.com")
        self.client.force_login(ana)
        from proyectos.models import Asignatura, Tecnologia

        self.client.post(reverse("proyectos:crear"), {
            "titulo": unicodedata.normalize("NFD", TITULO),
            "resumen": unicodedata.normalize("NFD", "Pingüinos y ñandúes"),
            "descripcion": "Descripción",
            "asignatura": Asignatura.objects.first().pk,
            "tecnologias": [Tecnologia.objects.first().pk],
            "repositorio": "https://github.com/uteq/x",
        })
        proyecto = Proyecto.objects.get()
        self.assertEqual(proyecto.titulo, TITULO)
        self.assertEqual(proyecto.resumen, "Pingüinos y ñandúes")


class PortadaYCertificadoTests(MediaTemporal, TestCase):
    def test_la_portada_de_color_muestra_el_titulo_completo_con_tildes(self):
        ana = crear_usuario("ana@correo.com")
        titulo = "Diseño de ñandúes: árbol, pingüino y «más» ¿sí?"
        crear_proyecto(ana, titulo=unicodedata.normalize("NFD", titulo), estado=Estado.APROBADO, color_portada="terracota")
        html = self.client.get(reverse("vitrina:explorar")).content.decode()
        # El título va escrito en HTML (no en una imagen), en NFC, dentro de la portada de color
        self.assertIn("data-vista-titulo", html)
        self.assertIn("Diseño de ñandúes: árbol, pingüino y «más» ¿sí?</p>", html)
        self.assertIn("Vitrina de Proyectos · UTEQ", html)
        self.assertIn("background-color: #9a3412", html)

    def test_con_imagen_de_portada_no_sale_la_portada_de_color(self):
        ana = crear_usuario("ana@correo.com")
        proyecto = crear_proyecto(ana, titulo="Con imagen", estado=Estado.APROBADO)
        proyecto.imagen_portada.save("p.png", imagen_png(), save=True)
        for url in (reverse("vitrina:explorar"), proyecto.get_absolute_url()):
            html = self.client.get(url).content.decode()
            self.assertIn(proyecto.imagen_portada.url, html)
            self.assertNotIn("data-vista-titulo", html)

    def test_el_certificado_se_genera_con_el_titulo_de_ejemplo(self):
        ana = crear_usuario("ana@correo.com")
        profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        proyecto = crear_proyecto(ana, titulo=unicodedata.normalize("NFD", TITULO) + " →", estado=Estado.APROBADO,
                                  codigo="VP-2026-0101", revisor=profe)
        from django.utils import timezone

        Proyecto.objects.filter(pk=proyecto.pk).update(aprobado_en=timezone.now())
        respuesta = self.client.get(reverse("vitrina:certificado", args=["VP-2026-0101"]))
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        self.assertTrue(io.BytesIO(respuesta.content).read(5) == b"%PDF-")
