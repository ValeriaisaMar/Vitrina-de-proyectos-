"""Spec 008, historia 5: identidad visual (logos, sellos, favicon y vista previa al compartir)."""

from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado, Imagen
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import MediaTemporal, crear_proyecto, imagen_png, tomar
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
        tomar(self.proyecto, self.profe)
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

    def _logo_incrustado(self, correo):
        """Comprueba que el HTML pide cid:logo-uteq y que el PNG viaja dentro del correo."""
        mime = correo.message()
        html = next(p for p in mime.walk() if p.get_content_type() == "text/html").get_content()
        self.assertIn('src="cid:logo-uteq"', html)
        self.assertNotIn("127.0.0.1", html)
        imagenes = [p for p in mime.walk() if p.get_content_type() == "image/png"]
        self.assertEqual(len(imagenes), 1)
        self.assertEqual(imagenes[0]["Content-ID"], "<logo-uteq>")
        self.assertTrue(imagenes[0].get_content().startswith(b"\x89PNG"))
        self.assertIn("multipart/related", [p.get_content_type() for p in mime.walk()])

    def test_el_correo_de_activacion_lleva_el_logo_incrustado(self):
        from django.core import mail

        self.client.post(reverse("cuentas:registro"), {
            "nombres": "Ana", "apellidos": "Pérez", "email": "ana@correo.com",
            "password1": "una-clave-segura-123", "password2": "una-clave-segura-123",
        })
        self._logo_incrustado(mail.outbox[0])

    def test_el_correo_de_recuperacion_lleva_el_logo_incrustado(self):
        from django.core import mail

        crear_usuario(email="ana@correo.com")
        self.client.post(reverse("cuentas:recuperar"), {"email": "ana@correo.com"})
        self.assertEqual(len(mail.outbox), 1)
        self._logo_incrustado(mail.outbox[0])


class EstaticosConVersionTests(TestCase):
    """El CSS y el JS llevan ?v=<huella>: si cambian, el navegador no puede seguir usando la copia vieja."""

    def test_base_pide_css_y_js_con_version(self):
        import re

        html = self.client.get(reverse("vitrina:inicio")).content.decode()
        self.assertRegex(html, r'href="/static/css/app\.css\?v=[0-9a-f]{10}"')
        for js in ("tema", "selector", "menu"):
            self.assertRegex(html, rf'src="/static/js/{js}\.js\?v=[0-9a-f]{{10}}"')
        self.assertIsNone(re.search(r'href="/static/css/app\.css"', html))

    def test_la_huella_cambia_si_cambia_el_archivo(self):
        import tempfile
        from pathlib import Path

        from vitrina.templatetags.iconos import _huella

        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "a.css"
            archivo.write_text("a{}")
            uno = _huella(str(archivo), 1)
            archivo.write_text("b{}")
            self.assertNotEqual(uno, _huella(str(archivo), 2))

    def test_el_pie_con_sesion_no_ofrece_iniciar_sesion(self):
        usuario = crear_usuario()
        self.client.force_login(usuario)
        html = self.client.get(reverse("vitrina:explorar")).content.decode()
        pie = html[html.index("<footer"):]
        self.assertNotIn(reverse("cuentas:registro"), pie)
        self.assertIn(reverse("cuentas:perfil"), pie)
