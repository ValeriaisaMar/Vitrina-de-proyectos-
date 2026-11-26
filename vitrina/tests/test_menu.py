"""Spec 009, historia 6: menú de la cuenta con íconos y opciones rápidas."""

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado, SolicitudRevision
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto, periodo

INICIO = reverse("vitrina:inicio")


class OpcionesSegunRolTests(TestCase):
    def test_estudiante(self):
        self.client.force_login(crear_usuario("ana@correo.com"))
        respuesta = self.client.get(INICIO)
        for url in (reverse("proyectos:mis_proyectos"), reverse("proyectos:crear"), reverse("comunidad:guardados"), reverse("vitrina:panel")):
            self.assertContains(respuesta, f'href="{url}"')
        self.assertContains(respuesta, "Mi perfil")
        self.assertNotContains(respuesta, reverse("proyectos:solicitudes"))
        self.assertNotContains(respuesta, reverse("cuentas:usuarios"))

    def test_profesor_con_contadores_y_disponibilidad(self):
        profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        ana = crear_usuario("ana@correo.com")
        proyecto = crear_proyecto(ana)
        cambiar_estado(proyecto, Estado.ENVIADO, ana)
        SolicitudRevision.objects.create(proyecto=proyecto, profesor=profe)
        self.client.force_login(profe)
        respuesta = self.client.get(INICIO)
        self.assertContains(respuesta, "Solicitudes de revisión")
        self.assertContains(respuesta, "Bandeja de revisión")
        self.assertContains(respuesta, "Proyectos que revisé")
        self.assertContains(respuesta, "Estoy recibiendo proyectos")
        self.assertEqual(respuesta.context["menu_cuenta"], {"solicitudes": 1, "bandeja": 0})

    def test_admin_solo_sin_mi_perfil(self):
        self.client.force_login(crear_usuario("admin@correo.com", rol=Rol.ADMIN))
        respuesta = self.client.get(INICIO)
        for url in (reverse("cuentas:usuarios"), reverse("proyectos:bandeja"), reverse("proyectos:periodos"),
                    reverse("proyectos:planes"), reverse("cuentas:correo_envio")):
            self.assertContains(respuesta, url)
        self.assertNotContains(respuesta, "Mi perfil")

    def test_cabecera_con_rol_activo_y_periodo(self):
        periodo("2026-2", actual=True)
        self.client.force_login(crear_usuario("ana@correo.com", nombres="Ana", apellidos="Paz"))
        respuesta = self.client.get(INICIO)
        self.assertContains(respuesta, "Ana Paz")
        self.assertContains(respuesta, "Período académico actual: 2026-2")


class CambioDeRolTests(TestCase):
    def test_un_clic_desde_el_menu(self):
        persona = crear_usuario("doble@correo.com", roles=["estudiante", "profesor"])
        self.client.force_login(persona)
        respuesta = self.client.get(INICIO)
        self.assertContains(respuesta, "Cambiar de rol")
        self.assertContains(respuesta, 'name="rol" value="profesor"')
        self.assertRedirects(self.client.post(reverse("cuentas:cambiar_rol"), {"rol": "profesor"}), reverse("vitrina:panel"))
        self.assertContains(self.client.get(INICIO), reverse("proyectos:solicitudes"))

    def test_con_un_rol_solo_la_etiqueta(self):
        self.client.force_login(crear_usuario("ana@correo.com"))
        self.assertNotContains(self.client.get(INICIO), "Cambiar de rol")


class VisitanteTests(TestCase):
    def test_ve_el_engranaje_con_tema_e_idioma(self):
        respuesta = self.client.get(INICIO)
        self.assertContains(respuesta, "Tema e idioma")
        self.assertContains(respuesta, "data-boton-tema")
        self.assertContains(respuesta, 'action="/i18n/setlang/"')
        self.assertContains(respuesta, reverse("cuentas:entrar"))
        self.assertContains(respuesta, reverse("cuentas:registro"))
        self.assertNotContains(respuesta, "Menú de la cuenta")


class MiCuentaSinJavaScriptTests(TestCase):
    def test_el_avatar_lleva_a_mi_cuenta_con_las_mismas_opciones(self):
        self.client.force_login(crear_usuario("ana@correo.com"))
        url = reverse("cuentas:mi_cuenta")
        self.assertContains(self.client.get(INICIO), f'href="{url}" data-menu-boton aria-haspopup="true"')
        respuesta = self.client.get(url)
        self.assertContains(respuesta, reverse("proyectos:mis_proyectos"))
        self.assertContains(respuesta, reverse("cuentas:salir"))

    def test_mi_cuenta_pide_sesion(self):
        self.assertEqual(self.client.get(reverse("cuentas:mi_cuenta")).status_code, 302)


class ContadoresTests(TestCase):
    def test_una_consulta_por_contador_aunque_haya_muchas_solicitudes(self):
        profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        ana = crear_usuario("ana@correo.com")
        self.client.force_login(profe)
        self.client.get(INICIO)

        def contar():
            with CaptureQueriesContext(connection) as consultas:
                self.client.get(INICIO)
            return len(consultas)

        antes = contar()
        for i in range(4):
            proyecto = crear_proyecto(ana, titulo=f"P{i}")
            cambiar_estado(proyecto, Estado.ENVIADO, ana)
            SolicitudRevision.objects.create(proyecto=proyecto, profesor=profe)
        self.assertEqual(contar(), antes)
