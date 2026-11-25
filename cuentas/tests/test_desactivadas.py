"""Una cuenta que un admin desactivó no puede reactivarse sola con un enlace de activación."""

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cuentas.correos import enlace_activacion
from cuentas.tests.utilidades import CLAVE, crear_usuario


class CuentaDesactivadaTests(TestCase):
    def setUp(self):
        # Entró alguna vez (last_login) y luego un admin la desactivó
        self.usuario = crear_usuario("suspendida@correo.com", activo=False, last_login=timezone.now())

    def test_no_recibe_enlace_de_activacion(self):
        respuesta = self.client.post(reverse("cuentas:reenviar"), {"email": self.usuario.email})
        self.assertRedirects(respuesta, reverse("cuentas:revisa_correo"))  # responde igual que siempre
        self.assertEqual(len(mail.outbox), 0)

    def test_un_enlace_valido_no_la_reactiva(self):
        enlace = enlace_activacion(self.client.get("/").wsgi_request, self.usuario)
        respuesta = self.client.get(enlace)
        self.assertEqual(respuesta.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_active)

    def test_al_entrar_se_le_dice_que_esta_desactivada(self):
        respuesta = self.client.post(reverse("cuentas:entrar"), {"username": self.usuario.email, "password": CLAVE})
        self.assertContains(respuesta, "Tu cuenta está desactivada")
        self.assertNotContains(respuesta, "Abre el enlace")

    def test_una_cuenta_nueva_sin_activar_si_recibe_el_enlace(self):
        crear_usuario("nueva@correo.com", activo=False)
        self.client.post(reverse("cuentas:reenviar"), {"email": "nueva@correo.com"})
        self.assertEqual(len(mail.outbox), 1)
