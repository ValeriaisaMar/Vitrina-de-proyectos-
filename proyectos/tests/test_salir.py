"""Un coautor puede salir de un proyecto mientras se pueda editar; el creador recibe un aviso."""

from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto, tomar


class SalirTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora")
        self.proyecto = crear_proyecto(self.ana, coautores=[self.luis])
        self.url = reverse("proyectos:salir", args=[self.proyecto.slug])

    def test_pide_confirmacion(self):
        self.client.force_login(self.luis)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Sí, salir del proyecto")
        self.assertIn(self.luis, self.proyecto.autores.all())

    def test_el_coautor_sale_y_se_avisa_al_creador(self):
        self.client.force_login(self.luis)
        respuesta = self.client.post(self.url)
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))
        self.assertEqual(list(self.proyecto.autores.all()), [self.ana])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@correo.com"])
        self.assertIn("Luis Mora", mail.outbox[0].subject)
        # Ya no lo ve: un borrador solo lo ven sus autores y los docentes
        self.assertEqual(self.client.get(self.proyecto.get_absolute_url()).status_code, 404)

    def test_mis_proyectos_muestra_salir_solo_al_coautor(self):
        self.client.force_login(self.luis)
        self.assertContains(self.client.get(reverse("proyectos:mis_proyectos")), self.url)
        self.client.force_login(self.ana)
        self.assertNotContains(self.client.get(reverse("proyectos:mis_proyectos")), self.url)

    def test_el_creador_no_puede_salir(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertIn(self.ana, self.proyecto.autores.all())

    def test_quien_no_es_autor_no_puede(self):
        self.client.force_login(crear_usuario("otra@correo.com"))
        self.assertEqual(self.client.post(self.url).status_code, 403)

    def test_con_observaciones_si_puede_salir(self):
        profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        tomar(self.proyecto, profe)
        cambiar_estado(self.proyecto, Estado.CON_OBSERVACIONES, profe, "Faltan pruebas")
        self.client.force_login(self.luis)
        self.assertRedirects(self.client.post(self.url), reverse("proyectos:mis_proyectos"))

    def test_despues_de_enviar_ya_no_puede_salir(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        self.client.force_login(self.luis)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertIn(self.luis, self.proyecto.autores.all())

    def test_si_el_correo_falla_igual_sale(self):
        self.client.force_login(self.luis)
        with mock.patch("django.core.mail.EmailMessage.send", side_effect=OSError("sin red")):
            self.client.post(self.url)
        self.assertEqual(list(self.proyecto.autores.all()), [self.ana])

