"""Pruebas de la portada con y sin proyectos aprobados."""

from django.test import TestCase
from django.urls import reverse

from cuentas.tests.utilidades import CLAVE, crear_usuario
from proyectos.models import Estado
from proyectos.tests.utilidades import crear_proyecto


class PortadaTests(TestCase):
    def test_sin_proyectos_invita_a_subir_el_primero(self):
        respuesta = self.client.get(reverse("vitrina:inicio"))
        self.assertContains(respuesta, "primer proyecto")
        self.assertEqual(respuesta.context["cifras"]["verificados"], 0)

    def test_con_proyectos_muestra_cifras_y_destacados(self):
        ana = crear_usuario("ana@correo.com")
        luis = crear_usuario("luis@correo.com")
        crear_proyecto(ana, titulo="Uno", estado=Estado.APROBADO, coautores=[luis], tecnologias=("Django", "Python"))
        crear_proyecto(ana, titulo="Dos", estado=Estado.APROBADO)
        crear_proyecto(ana, titulo="Borrador oculto")
        respuesta = self.client.get(reverse("vitrina:inicio"))
        cifras = respuesta.context["cifras"]
        self.assertEqual((cifras["verificados"], cifras["autores"], cifras["tecnologias"]), (2, 2, 2))
        self.assertContains(respuesta, "Proyectos destacados")
        self.assertNotContains(respuesta, "Borrador oculto")

    def test_el_estudiante_ve_mis_proyectos_en_el_menu(self):
        ana = crear_usuario("ana@correo.com")
        self.client.login(username=ana.email, password=CLAVE)
        self.assertContains(self.client.get(reverse("vitrina:inicio")), reverse("proyectos:mis_proyectos"))
