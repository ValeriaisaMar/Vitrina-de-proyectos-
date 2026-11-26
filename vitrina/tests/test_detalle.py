"""Pruebas de la ficha de un proyecto: quién la ve y qué muestra."""

from django.test import TestCase

from cuentas.models import Rol
from cuentas.tests.utilidades import CLAVE, crear_usuario
from proyectos.models import Estado
from proyectos.tests.utilidades import crear_proyecto, tomar


class DetalleTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora")

    def entrar(self, usuario):
        self.client.login(username=usuario.email, password=CLAVE)

    def test_un_aprobado_lo_ve_cualquiera(self):
        proyecto = crear_proyecto(self.ana, estado=Estado.APROBADO, coautores=[self.luis])
        respuesta = self.client.get(proyecto.get_absolute_url())
        self.assertContains(respuesta, proyecto.titulo)
        self.assertContains(respuesta, "Luis Mora")
        self.assertContains(respuesta, "https://github.com/uteq/gestor")
        self.assertNotContains(respuesta, "Vista previa")
        self.assertNotContains(respuesta, "Editar proyecto")

    def test_un_borrador_es_404_para_visitantes_y_otros_estudiantes(self):
        proyecto = crear_proyecto(self.ana)
        self.assertEqual(self.client.get(proyecto.get_absolute_url()).status_code, 404)
        self.entrar(crear_usuario("otra@correo.com"))
        self.assertEqual(self.client.get(proyecto.get_absolute_url()).status_code, 404)

    def test_el_autor_ve_la_vista_previa_y_puede_editar(self):
        proyecto = crear_proyecto(self.ana)
        self.entrar(self.ana)
        respuesta = self.client.get(proyecto.get_absolute_url())
        self.assertContains(respuesta, "Vista previa")
        self.assertContains(respuesta, "Editar proyecto")

    def test_un_profesor_ve_la_vista_previa_sin_editar(self):
        proyecto = crear_proyecto(self.ana, estado=Estado.ENVIADO)
        self.entrar(crear_usuario("profe@correo.com", rol=Rol.PROFESOR))
        respuesta = self.client.get(proyecto.get_absolute_url())
        self.assertContains(respuesta, "Vista previa")
        self.assertNotContains(respuesta, "Editar proyecto")

    def test_slug_inexistente(self):
        self.assertEqual(self.client.get("/proyecto/no-existe/").status_code, 404)


class DetalleRevisionTests(TestCase):
    """Lo que el módulo 004 agrega al detalle: botones de autor, observaciones e historial."""

    def setUp(self):
        from proyectos.servicios import cambiar_estado

        self.cambiar = cambiar_estado
        self.ana = crear_usuario("ana@correo.com")
        self.profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR, nombres="Carla", apellidos="Vera")
        self.proyecto = crear_proyecto(self.ana)
        self.cambiar(self.proyecto, Estado.ENVIADO, self.ana)
        tomar(self.proyecto, self.profe)  # el profesor asignado empieza la revisión (spec 009)

    def test_el_autor_ve_la_observacion_y_puede_reenviar(self):
        self.cambiar(self.proyecto, Estado.CON_OBSERVACIONES, self.profe, "Agrega capturas")
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(respuesta, "Agrega capturas")
        self.assertContains(respuesta, "Carla Vera pidió cambios")
        self.assertContains(respuesta, "Reenviar a revisión")
        self.assertContains(respuesta, "Historial")

    def test_el_publico_no_ve_el_historial_de_un_aprobado(self):
        self.cambiar(self.proyecto, Estado.APROBADO, self.profe, "Comentario interno")
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, "Comentario interno")
        self.assertNotContains(respuesta, "titulo-historial")
        self.proyecto.refresh_from_db()
        self.assertContains(respuesta, self.proyecto.codigo)

    def test_el_docente_tiene_enlace_a_la_revision(self):
        self.client.force_login(self.profe)
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(respuesta, f"/proyectos/{self.proyecto.slug}/revisar/")
