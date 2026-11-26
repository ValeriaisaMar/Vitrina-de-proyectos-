"""Spec 009, historia 4: enlaces a los perfiles y búsqueda de personas en Explorar."""

from django.test import TestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado
from proyectos.tests.utilidades import crear_proyecto

EXPLORAR = reverse("vitrina:explorar")


class BusquedaTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com", nombres="Ana María", apellidos="Paz Vera")
        self.admin = crear_usuario("admin@correo.com", nombres="Ana", apellidos="Admin", rol=Rol.ADMIN)
        crear_proyecto(self.ana, titulo="Gestor de tutorías", estado=Estado.APROBADO)
        crear_proyecto(crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora"), titulo="Otra cosa", estado=Estado.APROBADO)

    def titulos(self, respuesta):
        return [p.titulo for p in respuesta.context["pagina"].object_list]

    def test_busca_por_nombre_completo_del_autor(self):
        respuesta = self.client.get(EXPLORAR, {"q": "María Paz"})
        self.assertEqual(self.titulos(respuesta), ["Gestor de tutorías"])

    def test_sigue_buscando_por_titulo(self):
        self.assertEqual(self.titulos(self.client.get(EXPLORAR, {"q": "Gestor"})), ["Gestor de tutorías"])

    def test_bloque_personas_sin_admins(self):
        respuesta = self.client.get(EXPLORAR, {"q": "Ana"})
        self.assertContains(respuesta, "Personas")
        self.assertEqual([p.usuario for p in respuesta.context["personas"]], [self.ana])
        self.assertContains(respuesta, self.ana.perfil.get_absolute_url())


class EnlacesAPerfilesTests(TestCase):
    def test_autores_y_revisor_enlazan_a_su_perfil(self):
        ana = crear_usuario("ana@correo.com")
        profe = crear_usuario("profe@correo.com", nombres="Rosa", apellidos="Vera", rol=Rol.PROFESOR)
        proyecto = crear_proyecto(ana, estado=Estado.APROBADO, revisor=profe, codigo="VP-2026-0500")
        respuesta = self.client.get(proyecto.get_absolute_url())
        self.assertContains(respuesta, f'href="{ana.perfil.get_absolute_url()}"')
        self.assertContains(respuesta, f'href="{profe.perfil.get_absolute_url()}"')

    def test_un_admin_sin_perfil_no_tiene_enlace(self):
        admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.assertEqual(admin.url_perfil, "")
