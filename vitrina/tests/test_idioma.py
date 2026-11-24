"""Pruebas del cambio de idioma español/inglés."""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

# Textos de interfaz en español que NO deben aparecer cuando la página está en inglés.
TEXTOS_EN_ESPANOL = [
    "Saltar al contenido", "Iniciar sesión", "Crear cuenta", "Cómo funciona",
    "Sube tu proyecto", "Un docente lo revisa", "Queda verificado", "Explorar proyectos",
    "¿Tienes un proyecto de la carrera?", "Volver al inicio",
]


class IdiomaTests(TestCase):
    def elegir_ingles(self, siguiente="/"):
        return self.client.post(reverse("set_language"), {"language": "en", "next": siguiente})

    def test_espanol_por_defecto(self):
        respuesta = self.client.get("/")
        self.assertContains(respuesta, '<html lang="es">')
        self.assertContains(respuesta, "Saltar al contenido")

    def test_el_idioma_del_navegador_no_cambia_el_predeterminado(self):
        respuesta = self.client.get("/", headers={"accept-language": "en-US,en;q=0.9"})
        self.assertContains(respuesta, '<html lang="es">')

    def test_idioma_no_soportado_cae_en_espanol(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "fr"
        respuesta = self.client.get("/")
        self.assertContains(respuesta, '<html lang="es">')

    def test_cambiar_a_ingles_vuelve_a_la_misma_pagina(self):
        respuesta = self.elegir_ingles("/explorar/")
        self.assertRedirects(respuesta, "/explorar/")
        self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, "en")

    def test_en_ingles_no_quedan_textos_en_espanol(self):
        self.elegir_ingles()
        respuesta = self.client.get("/")
        self.assertContains(respuesta, '<html lang="en">')
        self.assertContains(respuesta, "Software Engineering projects,")
        self.assertContains(respuesta, "Skip to content")
        for texto in TEXTOS_EN_ESPANOL:
            self.assertNotContains(respuesta, texto)

    def test_el_ingles_se_mantiene_al_navegar(self):
        self.elegir_ingles()
        self.assertContains(self.client.get("/verificar/"), "Coming soon")

    def test_el_selector_marca_el_idioma_activo(self):
        respuesta = self.client.get("/")
        self.assertContains(respuesta, 'value="es" lang="es"')
        self.assertRegex(respuesta.content.decode(), r'value="es"[^>]*aria-pressed="true"')
        self.assertRegex(respuesta.content.decode(), r'value="en"[^>]*aria-pressed="false"')
