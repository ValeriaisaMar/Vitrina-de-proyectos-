"""Spec 008, historia 5: identidad visual (logos, sellos, favicon y vista previa al compartir)."""

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado, Imagen
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import MediaTemporal, crear_proyecto, imagen_png
from vitrina.verificacion import _logo, _sellos, certificado_pdf


class ArchivosDeMarcaTests(TestCase):
    def test_estan_en_static(self):
        for ruta in ("img/favicon.ico", "img/compartir.png", "img/logo-uteq.png", "img/logo-uteq-blanco.webp",
                     "img/iconos/site.webmanifest", "img/iconos/apple-touch-icon.png",
                     "img/marca/sello-carrera-128.png", "img/marca/sello-facultad-pdf.png", "img/marca/uteq-correo.png"):
            with self.subTest(ruta=ruta):
                self.assertIsNotNone(finders.find(ruta))


class CabeceraYPieTests(TestCase):
    def setUp(self):
        self.respuesta = self.client.get(reverse("vitrina:inicio"))

    def test_favicon_manifest_y_vista_previa(self):
        for texto in ('rel="icon"', 'rel="apple-touch-icon"', 'rel="manifest"', 'name="theme-color"',
                      'property="og:title"', 'property="og:image" content="http://testserver/static/img/compartir.png"'):
            self.assertContains(self.respuesta, texto)
        self.assertContains(self.respuesta, 'name="theme-color"', count=1)  # sin duplicados

    def test_logo_claro_y_oscuro_con_tamano(self):
        self.assertContains(self.respuesta, "img/logo-uteq.png")
        self.assertContains(self.respuesta, "img/logo-uteq-blanco.png")
        self.assertContains(self.respuesta, 'type="image/webp"')
        self.assertContains(self.respuesta, 'width="376" height="120"')

    def test_pie_con_los_dos_sellos(self):
        self.assertContains(self.respuesta, "img/marca/sello-facultad-128.png")
        self.assertContains(self.respuesta, "img/marca/sello-carrera-128.png")
        self.assertContains(self.respuesta, "Carrera de Software")


class SelloEnCuentasTests(TestCase):
    def test_entrar_registro_y_recuperar_llevan_el_sello(self):
        for nombre in ("cuentas:entrar", "cuentas:registro", "cuentas:recuperar", "cuentas:reenviar"):
            with self.subTest(pagina=nombre):
                self.assertContains(self.client.get(reverse(nombre)), "img/marca/sello-carrera-128.png")


class VistaPreviaDeProyectoTests(MediaTemporal, TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.profe = crear_usuario("profe@correo.com", rol="profesor")
        self.proyecto = crear_proyecto(self.ana, titulo="Gestor de tutorías")
        Imagen.objects.create(proyecto=self.proyecto, archivo=imagen_png())

    def aprobar(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        cambiar_estado(self.proyecto, Estado.EN_REVISION, self.profe)
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe)

    def test_proyecto_aprobado_comparte_titulo_resumen_y_portada(self):
        self.aprobar()
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(respuesta, '<meta property="og:title" content="Gestor de tutorías">', html=False)
        self.assertContains(respuesta, f'content="{self.proyecto.resumen}"')
        self.assertContains(respuesta, 'property="og:image" content="http://testserver/media/proyectos/imagenes/')

    def test_un_borrador_no_comparte_sus_datos(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertNotContains(respuesta, 'content="Gestor de tutorías"')

    def test_verificacion_con_logo_y_sellos(self):
        self.aprobar()
        respuesta = self.client.get(reverse("vitrina:verificar_codigo", args=[self.proyecto.codigo]))
        self.assertContains(respuesta, "img/logo-uteq-blanco.png")
        self.assertContains(respuesta, "img/marca/sello-facultad-128.png")
        self.assertContains(respuesta, "img/marca/sello-carrera-128.png")

    def test_certificado_con_logo_y_sellos(self):
        self.aprobar()
        self.assertIsNotNone(_logo())
        self.assertEqual(len(_sellos()), 2)
        pdf = certificado_pdf(self.proyecto, "http://testserver/verificar/x/")
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreaterEqual(pdf.count(b"/Subtype /Image"), 3)  # logo, dos sellos (y el QR)


class ErroresYCorreosTests(TestCase):
    def test_la_pagina_500_lleva_el_logo_sin_procesadores_de_contexto(self):
        html = render_to_string("500.html")
        self.assertIn("/static/img/logo-uteq.png", html)
        self.assertIn('alt="UTEQ"', html)

    def test_los_correos_html_llevan_el_logo_con_direccion_absoluta(self):
        from django.core import mail

        self.client.post(reverse("cuentas:registro"), {
            "nombres": "Ana", "apellidos": "Pérez", "email": "ana@correo.com",
            "password1": "una-clave-segura-123", "password2": "una-clave-segura-123",
        })
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('src="http://testserver/static/img/marca/uteq-correo.png"', html)

    def test_la_recuperacion_usa_protocolo_y_dominio(self):
        html = render_to_string("cuentas/correos/recuperacion.html", {
            "protocol": "https", "domain": "vitrina.uteq.edu.ec", "uid": "x", "token": "y",
            "user": crear_usuario(), "request": RequestFactory().get("/"),
        })
        self.assertIn("https://vitrina.uteq.edu.ec/static/img/marca/uteq-correo.png", html)
