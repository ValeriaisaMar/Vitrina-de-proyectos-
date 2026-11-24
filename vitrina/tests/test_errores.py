"""Pruebas de las páginas de error 404 y 500."""

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import path


def vista_que_falla(request):
    raise RuntimeError("detalle interno que no debe verse")


urlpatterns = [path("falla/", vista_que_falla)]


@override_settings(DEBUG=False)
class Error404Tests(TestCase):
    def test_404_con_el_diseno(self):
        respuesta = self.client.get("/esta-pagina-no-existe/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertTemplateUsed(respuesta, "404.html")
        self.assertContains(respuesta, "No encontramos esta página", status_code=404)
        self.assertContains(respuesta, "Volver al inicio", status_code=404)

    def test_404_en_ingles(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        respuesta = self.client.get("/esta-pagina-no-existe/")
        self.assertContains(respuesta, "We couldn't find this page", status_code=404)


@override_settings(DEBUG=False, ROOT_URLCONF=__name__)
class Error500Tests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_500_sin_detalles_tecnicos(self):
        respuesta = self.client.get("/falla/")
        self.assertEqual(respuesta.status_code, 500)
        self.assertContains(respuesta, "Algo salió mal", status_code=500)
        self.assertNotContains(respuesta, "detalle interno", status_code=500)
        self.assertNotContains(respuesta, "Traceback", status_code=500)
