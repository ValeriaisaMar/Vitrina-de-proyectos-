"""Pruebas de la portada, las páginas "Próximamente" y la plantilla base."""

from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class PortadaTests(TestCase):
    def setUp(self):
        self.respuesta = self.client.get(reverse("vitrina:inicio"))

    def test_responde_y_usa_la_plantilla_base(self):
        self.assertEqual(self.respuesta.status_code, 200)
        self.assertTemplateUsed(self.respuesta, "base.html")
        self.assertTemplateUsed(self.respuesta, "vitrina/inicio.html")

    def test_encabezado_completo(self):
        for texto in ("Vitrina de Proyectos", "Explorar", "Verificar QR", "Iniciar sesión", "Crear cuenta"):
            self.assertContains(self.respuesta, texto)
        self.assertContains(self.respuesta, reverse("vitrina:explorar"))
        self.assertContains(self.respuesta, reverse("vitrina:verificar"))
        self.assertContains(self.respuesta, 'action="/i18n/setlang/"')
        self.assertContains(self.respuesta, "data-boton-tema")

    def test_inicio_marcado_como_pagina_actual(self):
        self.assertContains(self.respuesta, 'aria-current="page"')

    def test_secciones_de_la_portada(self):
        self.assertContains(self.respuesta, 'id="titulo-portada"')
        self.assertContains(self.respuesta, 'id="como-funciona"')
        for numero in ("01", "02", "03", "04"):
            self.assertContains(self.respuesta, f">{numero}<")
        self.assertContains(self.respuesta, "¿Tienes un proyecto de la carrera?")
        self.assertContains(self.respuesta, "Universidad Técnica Estatal de Quevedo")  # pie

    def test_enlace_para_saltar_al_contenido(self):
        self.assertContains(self.respuesta, 'href="#contenido"')
        self.assertContains(self.respuesta, 'id="contenido"')

    def test_menu_movil_funciona_sin_javascript(self):
        self.assertContains(self.respuesta, "<details")
        self.assertContains(self.respuesta, "<summary")

    def test_el_tema_se_aplica_antes_de_cargar_el_css(self):
        html = self.respuesta.content.decode()
        self.assertLess(html.index('localStorage.getItem("tema")'), html.index("css/app.css"))

    def test_sin_logo_se_muestra_el_nombre_y_no_una_imagen_rota(self):
        self.assertNotContains(self.respuesta, 'alt="UTEQ"')

    def test_con_logo_se_muestra_la_imagen(self):
        with mock.patch("config.contexto.finders.find", return_value="/ruta/logo.svg"):
            respuesta = self.client.get(reverse("vitrina:inicio"))
        self.assertContains(respuesta, 'alt="UTEQ"')


class ProximamenteTests(TestCase):
    def test_explorar_y_verificar_muestran_proximamente(self):
        for nombre in ("vitrina:explorar", "vitrina:verificar"):
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, "Próximamente")
            self.assertTemplateUsed(respuesta, "base.html")


class EstilosTests(TestCase):
    """Comprueba que el CSS compilado esté en el repositorio y tenga lo que pide la spec."""

    def setUp(self):
        self.css = (Path(settings.BASE_DIR) / "static" / "css" / "app.css").read_text(encoding="utf-8")

    def test_colores_institucionales_exactos(self):
        self.assertIn("#025a27", self.css)
        self.assertIn("#ecb932", self.css)

    def test_respeta_reducir_movimiento(self):
        self.assertIn("prefers-reduced-motion", self.css)

    def test_fuentes_locales(self):
        self.assertIn("Unbounded", self.css)
        self.assertIn("Archivo", self.css)
        self.assertNotIn("fonts.googleapis.com", self.css)
