"""El creador puede pasarle el proyecto a un coautor y quedar como coautor."""

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto


class TransferirTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora")
        self.proyecto = crear_proyecto(self.ana, coautores=[self.luis])
        self.url = reverse("proyectos:transferir", args=[self.proyecto.slug])

    def test_muestra_a_los_coautores(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "luis@correo.com")
        self.assertNotContains(respuesta, 'value="%s"' % self.ana.pk)

    def test_transfiere_y_el_anterior_queda_como_coautor(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(self.url, {"nuevo_creador": self.luis.pk})
        self.assertRedirects(respuesta, reverse("proyectos:mis_proyectos"))
        self.assertEqual(self.proyecto.creador, self.luis)
        self.assertEqual(set(self.proyecto.autores.all()), {self.ana, self.luis})
        self.assertEqual(self.proyecto.autorias.filter(es_creador=True).count(), 1)
        self.assertEqual(mail.outbox[0].to, ["luis@correo.com"])

    def test_el_nuevo_creador_tiene_los_permisos_y_el_anterior_los_pierde(self):
        self.client.force_login(self.ana)
        self.client.post(self.url, {"nuevo_creador": self.luis.pk})
        # Ana ya no puede eliminar; ahora puede salir
        self.assertEqual(self.client.post(reverse("proyectos:eliminar", args=[self.proyecto.slug])).status_code, 403)
        self.assertEqual(self.client.get(reverse("proyectos:salir", args=[self.proyecto.slug])).status_code, 200)
        self.client.force_login(self.luis)
        self.assertEqual(self.client.get(reverse("proyectos:eliminar", args=[self.proyecto.slug])).status_code, 200)

    def test_un_coautor_no_puede_transferir(self):
        self.client.force_login(self.luis)
        self.assertEqual(self.client.post(self.url, {"nuevo_creador": self.luis.pk}).status_code, 403)
        self.assertEqual(self.proyecto.creador, self.ana)

    def test_no_se_transfiere_a_alguien_que_no_es_coautor(self):
        otra = crear_usuario("otra@correo.com")
        self.client.force_login(self.ana)
        respuesta = self.client.post(self.url, {"nuevo_creador": otra.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("nuevo_creador", respuesta.context["form"].errors)
        self.assertEqual(self.proyecto.creador, self.ana)

    def test_sin_coautores_no_hay_a_quien_transferir(self):
        solo = crear_proyecto(self.ana, titulo="Proyecto sin coautores")
        self.client.force_login(self.ana)
        url = reverse("proyectos:transferir", args=[solo.slug])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertNotContains(self.client.get(reverse("proyectos:mis_proyectos")), url)

    def test_despues_de_enviar_no_se_transfiere(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(self.url, {"nuevo_creador": self.luis.pk}).status_code, 403)

    def test_con_observaciones_si_se_transfiere(self):
        profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        cambiar_estado(self.proyecto, Estado.EN_REVISION, profe)
        cambiar_estado(self.proyecto, Estado.CON_OBSERVACIONES, profe, "Faltan pruebas")
        self.client.force_login(self.ana)
        self.client.post(self.url, {"nuevo_creador": self.luis.pk})
        self.assertEqual(self.proyecto.creador, self.luis)

    def test_mis_proyectos_muestra_transferir_solo_al_creador(self):
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(reverse("proyectos:mis_proyectos")), self.url)
        self.client.force_login(self.luis)
        self.assertNotContains(self.client.get(reverse("proyectos:mis_proyectos")), self.url)
