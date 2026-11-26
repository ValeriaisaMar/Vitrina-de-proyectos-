"""Spec 009, historia 7: portada, color de la portada, proyecto desplegado y video."""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from PIL import Image

from cuentas.tests.utilidades import crear_usuario
from proyectos.forms import FormularioProyecto
from proyectos.models import Asignatura, Estado, Imagen, Proyecto, Tecnologia
from proyectos.paleta import PALETA, contraste_con_blanco
from proyectos.tests.utilidades import MediaTemporal, crear_proyecto, imagen_png


def jpg(nombre="portada.jpg", tam=(1600, 1600)):
    buffer = io.BytesIO()
    Image.new("RGB", tam, (200, 30, 30)).save(buffer, "JPEG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/jpeg")


class PaletaTests(TestCase):
    def test_entre_8_y_10_colores_con_contraste_suficiente(self):
        self.assertTrue(8 <= len(PALETA) <= 10)
        self.assertEqual(PALETA["verde"][1], "#025a27")  # incluye el verde institucional
        for clave, (_nombre, codigo) in PALETA.items():
            self.assertGreaterEqual(contraste_con_blanco(codigo), 4.5, clave)

    def test_la_portada_de_color_usa_el_color_elegido(self):
        proyecto = crear_proyecto(crear_usuario("ana@correo.com"), estado=Estado.APROBADO, color_portada="azul")
        self.assertContains(self.client.get(reverse("vitrina:explorar")), "background-color: #1e40af")
        self.assertEqual(proyecto.color_hex, "#1e40af")

    def test_no_acepta_un_color_fuera_de_la_paleta(self):
        form = FormularioProyecto({"color_portada": "#ff00ff"}, usuario=crear_usuario("ana@correo.com"))
        form.is_valid()
        self.assertIn("color_portada", form.errors)


class PortadaTests(MediaTemporal, TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.client.force_login(self.ana)

    def datos(self, **extra):
        return {
            "titulo": "Con portada", "resumen": "Resumen", "descripcion": "Descripción",
            "asignatura": Asignatura.objects.first().pk, "tecnologias": [Tecnologia.objects.first().pk],
            "repositorio": "https://github.com/uteq/x", "color_portada": "vino", **extra,
        }

    def test_subir_portada_la_recorta_a_16_9_en_webp(self):
        self.client.post(reverse("proyectos:crear"), self.datos(portada=jpg()))
        proyecto = Proyecto.objects.get()
        self.assertTrue(proyecto.imagen_portada.name.startswith("proyectos/portadas/"))
        self.assertTrue(proyecto.imagen_portada.name.endswith(".webp"))
        with Image.open(proyecto.imagen_portada.path) as imagen:
            self.assertEqual((imagen.format, imagen.size), ("WEBP", (1200, 675)))

    def test_una_imagen_falsa_se_rechaza(self):
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos(portada=SimpleUploadedFile("x.jpg", b"no")))
        self.assertContains(respuesta, "no es una imagen válida")
        self.assertFalse(Proyecto.objects.exists())

    def test_quitar_la_portada_vuelve_al_color(self):
        self.client.post(reverse("proyectos:crear"), self.datos(portada=jpg()))
        proyecto = Proyecto.objects.get()
        ruta = proyecto.imagen_portada.path
        self.client.post(reverse("proyectos:editar", args=[proyecto.slug]), self.datos(quitar_portada="on"))
        proyecto.refresh_from_db()
        self.assertFalse(proyecto.imagen_portada)
        import os

        self.assertFalse(os.path.exists(ruta))  # el archivo viejo se borra

    def test_la_portada_es_la_imagen_para_compartir(self):
        proyecto = crear_proyecto(self.ana, estado=Estado.APROBADO)
        Imagen.objects.create(proyecto=proyecto, archivo=imagen_png())
        self.assertIn("/proyectos/imagenes/", proyecto.url_imagen_compartir)  # sin portada: la captura
        self.client.post(reverse("proyectos:crear"), self.datos(portada=jpg()))
        con_portada = Proyecto.objects.get(titulo="Con portada")
        Proyecto.objects.filter(pk=con_portada.pk).update(estado=Estado.APROBADO)
        respuesta = self.client.get(con_portada.get_absolute_url())
        self.assertContains(respuesta, 'property="og:image" content="http://testserver/media/proyectos/portadas/')


class EnlacesTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")

    def test_desplegado_y_video_junto_al_repositorio(self):
        proyecto = crear_proyecto(self.ana, estado=Estado.APROBADO, demo="https://gestor.example.com",
                                  video="https://www.youtube.com/watch?v=abc")
        html = self.client.get(proyecto.get_absolute_url()).content.decode()
        self.assertIn("Ver proyecto desplegado", html)
        self.assertIn("Ver video", html)
        self.assertIn('href="https://www.youtube.com/watch?v=abc" target="_blank" rel="noopener noreferrer"', html)
        self.assertIn('href="https://gestor.example.com" target="_blank" rel="noopener noreferrer"', html)

    def test_vacios_no_se_muestran(self):
        proyecto = crear_proyecto(self.ana, estado=Estado.APROBADO)
        respuesta = self.client.get(proyecto.get_absolute_url())
        self.assertNotContains(respuesta, "Ver proyecto desplegado")
        self.assertNotContains(respuesta, "Ver video")

    def test_solo_http_y_https(self):
        for malo in ("javascript:alert(1)", "ftp://archivos.example.com/video.mp4", "data:text/html,hola"):
            form = FormularioProyecto({"video": malo, "demo": malo}, usuario=self.ana)
            form.is_valid()
            self.assertIn("video", form.errors, malo)
            self.assertIn("demo", form.errors, malo)


class MigracionPortadasTests(MediaTemporal, TransactionTestCase):
    """0018: la primera captura de la galería pasa a ser la portada."""

    serialized_rollback = True

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def otras(self):
        return [n for n in MigrationExecutor(connection).loader.graph.leaf_nodes() if n[0] != "proyectos"]

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_copia_la_primera_captura(self):
        apps = self.migrar([("proyectos", "0017_portada_color_video"), *self.otras()])
        Proyecto = apps.get_model("proyectos", "Proyecto")
        ImagenH = apps.get_model("proyectos", "Imagen")
        datos = {"resumen": "r", "descripcion": "d", "repositorio": "https://github.com/uteq/x",
                 "asignatura": apps.get_model("proyectos", "Asignatura").objects.first()}
        con = Proyecto.objects.create(titulo="Con", slug="mig-port-con", **datos)
        sin = Proyecto.objects.create(titulo="Sin", slug="mig-port-sin", **datos)
        ImagenH.objects.create(proyecto=con, archivo=imagen_png("captura.png", (800, 800)), orden=1)

        apps = self.migrar([("proyectos", "0018_portadas_desde_galeria"), *self.otras()])
        Proyecto = apps.get_model("proyectos", "Proyecto")
        con = Proyecto.objects.get(pk=con.pk)
        self.assertTrue(con.imagen_portada.name.endswith(".webp"))
        self.assertEqual(Proyecto.objects.get(pk=sin.pk).imagen_portada, "")
        apps.get_model("proyectos", "Imagen").objects.filter(proyecto__slug__startswith="mig-port-").delete()
        Proyecto.objects.filter(slug__startswith="mig-port-").delete()
