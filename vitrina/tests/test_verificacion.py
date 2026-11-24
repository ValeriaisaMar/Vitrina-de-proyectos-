"""Pruebas del módulo 005: código, página de verificación, QR y certificado."""

import io

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto
from vitrina.verificacion import normalizar_codigo, qr_png, url_verificacion


def aprobar(proyecto, autor, profe):
    cambiar_estado(proyecto, Estado.ENVIADO, autor)
    cambiar_estado(proyecto, Estado.EN_REVISION, profe)
    cambiar_estado(proyecto, Estado.APROBADO, profe, "Comentario interno del docente")
    proyecto.refresh_from_db()
    return proyecto


class NormalizarCodigoTests(TestCase):
    def test_formas_aceptadas(self):
        for texto in ("VP-2026-0007", " vp-2026-0007 ", "VP20260007", "vp 2026 0007"):
            self.assertEqual(normalizar_codigo(texto), "VP-2026-0007", texto)

    def test_formas_rechazadas(self):
        for texto in ("", "hola", "VP-26-0007", "XX-2026-0007", "VP-2026-07", "VP-2026-0007; DROP"):
            self.assertIsNone(normalizar_codigo(texto), texto)


class BaseVerificacion(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com", nombres="Ana", apellidos="Zambrano")
        self.profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR, nombres="Carla", apellidos="Vera")
        self.proyecto = aprobar(crear_proyecto(self.ana, titulo="Gestor de tutorías"), self.ana, self.profe)
        self.codigo = self.proyecto.codigo


class PaginaVerificacionTests(BaseVerificacion):
    def test_muestra_solo_los_datos_publicos(self):
        respuesta = self.client.get(reverse("vitrina:verificar_codigo", args=[self.codigo]))
        self.assertEqual(respuesta.status_code, 200)
        for dato in ("Gestor de tutorías", "Ana Zambrano", "Carla Vera", self.codigo, "Proyecto verificado"):
            self.assertContains(respuesta, dato)
        for privado in ("ana@correo.com", "profe@correo.com", "Comentario interno del docente"):
            self.assertNotContains(respuesta, privado)

    def test_codigo_inexistente(self):
        respuesta = self.client.get(reverse("vitrina:verificar_codigo", args=["VP-2026-9999"]))
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, "Código no válido", status_code=404)

    def test_texto_raro_en_la_url_se_escapa(self):
        respuesta = self.client.get("/verificar/%3Cb%3Ehola%3Ci%3E/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, "&lt;b&gt;hola&lt;i&gt;", status_code=404)
        self.assertNotContains(respuesta, "<b>hola<i>", status_code=404)

    def test_un_codigo_en_minusculas_redirige_al_canonico(self):
        respuesta = self.client.get(reverse("vitrina:verificar_codigo", args=[self.codigo.lower()]))
        self.assertRedirects(respuesta, reverse("vitrina:verificar_codigo", args=[self.codigo]), status_code=301)

    def test_el_formulario_lleva_al_resultado(self):
        respuesta = self.client.get(reverse("vitrina:verificar"), {"codigo": f"  {self.codigo.lower()} "})
        self.assertRedirects(respuesta, reverse("vitrina:verificar_codigo", args=[self.codigo]))

    def test_el_formulario_avisa_si_la_forma_es_incorrecta(self):
        respuesta = self.client.get(reverse("vitrina:verificar"), {"codigo": "hola"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "VP-2026-0001")
        self.assertIn("codigo", respuesta.context["form"].errors)

    def test_la_pagina_sin_codigo(self):
        respuesta = self.client.get(reverse("vitrina:verificar"))
        self.assertContains(respuesta, "Verificar un proyecto")
        self.assertFalse(respuesta.context["form"].errors)


class DescargasTests(BaseVerificacion):
    def test_el_qr_es_un_png(self):
        respuesta = self.client.get(reverse("vitrina:qr", args=[self.codigo]))
        self.assertEqual(respuesta["Content-Type"], "image/png")
        imagen = Image.open(io.BytesIO(respuesta.content))
        self.assertEqual(imagen.format, "PNG")
        self.assertNotIn("Content-Disposition", respuesta)

    def test_el_qr_se_descarga_con_nombre(self):
        respuesta = self.client.get(reverse("vitrina:qr", args=[self.codigo]) + "?descargar")
        self.assertIn(f'filename="{self.codigo}-qr.png"', respuesta["Content-Disposition"])

    def test_el_certificado_es_un_pdf(self):
        respuesta = self.client.get(reverse("vitrina:certificado", args=[self.codigo]))
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        self.assertTrue(respuesta.content.startswith(b"%PDF-"))
        self.assertIn(f'filename="{self.codigo}-certificado.pdf"', respuesta["Content-Disposition"])

    def test_el_certificado_sale_en_ingles(self):
        self.client.post(reverse("set_language"), {"language": "en", "next": "/"})
        respuesta = self.client.get(reverse("vitrina:certificado", args=[self.codigo]))
        self.assertEqual(respuesta.status_code, 200)

    def test_nada_para_proyectos_sin_aprobar(self):
        borrador = crear_proyecto(self.ana, titulo="Borrador")
        borrador.__class__.objects.filter(pk=borrador.pk).update(codigo="VP-2026-0500")  # código "colado"
        for nombre in ("vitrina:qr", "vitrina:certificado", "vitrina:verificar_codigo"):
            self.assertEqual(self.client.get(reverse(nombre, args=["VP-2026-0500"])).status_code, 404, nombre)

    def test_el_detalle_ofrece_las_descargas(self):
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(respuesta, reverse("vitrina:certificado", args=[self.codigo]))
        self.assertContains(respuesta, reverse("vitrina:qr", args=[self.codigo]))


class DireccionDelQrTests(TestCase):
    def test_usa_la_direccion_de_la_peticion(self):
        peticion = RequestFactory().get("/", HTTP_HOST="localhost")
        self.assertEqual(url_verificacion(peticion, "VP-2026-0001"), "http://localhost/verificar/VP-2026-0001/")

    @override_settings(SITIO_URL="http://192.168.1.20:8000")
    def test_usa_sitio_url_si_existe(self):
        peticion = RequestFactory().get("/", HTTP_HOST="localhost")
        self.assertEqual(url_verificacion(peticion, "VP-2026-0001"), "http://192.168.1.20:8000/verificar/VP-2026-0001/")

    def test_el_qr_codifica_la_direccion(self):
        png = qr_png("http://localhost/verificar/VP-2026-0001/")
        self.assertTrue(png.startswith(b"\x89PNG"))
