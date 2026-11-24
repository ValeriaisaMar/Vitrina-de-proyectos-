"""Pruebas de los paneles por rol (módulo 006)."""

from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Rol
from cuentas.tests.utilidades import CLAVE, crear_usuario
from proyectos.models import Estado
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto

URL = reverse("vitrina:panel")


class PanelBase(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR, nombres="Carla", apellidos="Vera")
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)

    def proyecto_en(self, estado, titulo, comentario="Agrega capturas"):
        p = crear_proyecto(self.ana, titulo=titulo)
        if estado == Estado.BORRADOR:
            return p
        cambiar_estado(p, Estado.ENVIADO, self.ana)
        if estado == Estado.ENVIADO:
            return p
        cambiar_estado(p, Estado.EN_REVISION, self.profe)
        if estado != Estado.EN_REVISION:
            cambiar_estado(p, estado, self.profe, comentario)
        p.refresh_from_db()
        return p


class AccesoTests(PanelBase):
    def test_sin_sesion_va_al_login(self):
        self.assertRedirects(self.client.get(URL), reverse("cuentas:entrar") + "?next=" + URL)

    def test_cada_rol_ve_su_panel(self):
        for usuario, plantilla in ((self.ana, "estudiante"), (self.profe, "profesor"), (self.admin, "admin")):
            self.client.force_login(usuario)
            self.assertTemplateUsed(self.client.get(URL), f"vitrina/paneles/{plantilla}.html")

    def test_al_entrar_llega_a_su_panel(self):
        respuesta = self.client.post(reverse("cuentas:entrar"), {"username": self.ana.email, "password": CLAVE})
        self.assertRedirects(respuesta, URL)

    def test_el_menu_tiene_mi_panel(self):
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(reverse("vitrina:inicio")), URL)


class PanelEstudianteTests(PanelBase):
    def test_cifras_y_pendientes(self):
        self.proyecto_en(Estado.BORRADOR, "Borrador uno")
        self.proyecto_en(Estado.ENVIADO, "Enviado uno")
        self.proyecto_en(Estado.CON_OBSERVACIONES, "Para corregir", comentario="Falta el manual")
        aprobado = self.proyecto_en(Estado.APROBADO, "Listo")
        self.client.force_login(self.ana)
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.context["cifras"], {
            "borradores": 1, "en_revision": 1, "observaciones": 1, "aprobados": 1, "total": 4,
        })
        self.assertContains(respuesta, "Falta el manual")
        self.assertContains(respuesta, "Carla Vera pidió cambios")
        self.assertContains(respuesta, reverse("proyectos:enviar", args=["borrador-uno"]))
        self.assertContains(respuesta, reverse("vitrina:certificado", args=[aprobado.codigo]))

    def test_solo_cuenta_sus_proyectos(self):
        crear_proyecto(crear_usuario("otra@correo.com"), titulo="Ajeno")
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(URL).context["cifras"]["total"], 0)

    def test_sin_proyectos_invita_a_crear(self):
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(URL), "Sube tu primer proyecto")

    def test_consultas_fijas(self):
        for i in range(3):
            self.proyecto_en(Estado.CON_OBSERVACIONES, f"Corregir {i}")
        self.client.force_login(self.ana)
        self.client.get(URL)  # calienta sesión y caché de tipos de contenido
        with self.assertNumQueries(7):
            self.client.get(URL)
        self.proyecto_en(Estado.CON_OBSERVACIONES, "Uno más")
        with self.assertNumQueries(7):
            self.client.get(URL)


class PanelProfesorTests(PanelBase):
    def test_cifras_y_listas(self):
        self.proyecto_en(Estado.ENVIADO, "Esperando")
        self.proyecto_en(Estado.EN_REVISION, "Tomado")
        self.proyecto_en(Estado.APROBADO, "Aprobado uno")
        self.proyecto_en(Estado.RECHAZADO, "Rechazado uno", comentario="No aplica")
        self.client.force_login(self.profe)
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.context["por_revisar"], 1)
        self.assertEqual(respuesta.context["mis_revisiones"], 1)
        self.assertEqual(respuesta.context["decisiones"], {"aprobados": 1, "observaciones": 0, "rechazados": 1})
        self.assertContains(respuesta, reverse("proyectos:tomar", args=["esperando"]))
        self.assertContains(respuesta, "Rechazado uno")


class PanelAdminTests(PanelBase):
    def test_cifras_globales(self):
        crear_usuario("nuevo@correo.com", activo=False)
        self.proyecto_en(Estado.BORRADOR, "B")
        self.proyecto_en(Estado.APROBADO, "A")
        self.client.force_login(self.admin)
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.context["usuarios"], {"estudiantes": 1, "profesores": 1, "admins": 1, "sin_activar": 1})
        estados = {fila["etiqueta"]: fila["valor"] for fila in respuesta.context["estados"]}
        self.assertEqual((estados["Borrador"], estados["Aprobado"]), (1, 1))
        self.assertEqual(respuesta.context["tecnologias"][0]["etiqueta"], "Django")
        self.assertContains(respuesta, reverse("cuentas:usuarios"))

    def test_avisa_los_proyectos_atrasados(self):
        hace_cinco_dias = timezone.now() - timedelta(days=5)
        with mock.patch("django.utils.timezone.now", return_value=hace_cinco_dias):
            self.proyecto_en(Estado.ENVIADO, "Olvidado")
        self.proyecto_en(Estado.ENVIADO, "Reciente")
        self.client.force_login(self.admin)
        respuesta = self.client.get(URL)
        self.assertEqual(respuesta.context["total_atrasados"], 1)
        self.assertContains(respuesta, "Olvidado")

    def test_barras_proporcionales(self):
        from vitrina.paneles import _barras

        self.assertEqual([f["ancho"] for f in _barras([("a", 4), ("b", 2), ("c", 0)])], [100, 50, 0])
        self.assertEqual(_barras([("a", 0)])[0]["ancho"], 0)
