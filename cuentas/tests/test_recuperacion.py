"""Historia 3: recuperar la contraseña por correo."""

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from cuentas.tests.utilidades import crear_usuario, enlace_en_correo

NUEVA = "otra-clave-muy-segura-456"


class RecuperacionTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario(email="luis@correo.com")

    def pedir(self, email):
        return self.client.post(reverse("cuentas:recuperar"), {"email": email}, follow=True)

    def test_envia_el_enlace_a_una_cuenta_activa(self):
        respuesta = self.pedir("Luis@Correo.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/cuentas/contrasena/nueva/", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        self.assertContains(respuesta, "Si el correo que escribiste tiene una cuenta activa")

    def test_responde_igual_si_el_correo_no_existe(self):
        respuesta = self.pedir("nadie@correo.com")
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(respuesta, "Si el correo que escribiste tiene una cuenta activa")

    def test_no_envia_a_cuentas_inactivas(self):
        crear_usuario(email="pendiente@correo.com", activo=False)
        self.pedir("pendiente@correo.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_el_enlace_permite_crear_una_contrasena_nueva_una_sola_vez(self):
        self.pedir("luis@correo.com")
        enlace = enlace_en_correo(mail.outbox[0])

        formulario = self.client.get(enlace, follow=True)  # Django redirige a una URL sin el token
        self.assertContains(formulario, "Crea tu nueva contraseña")
        respuesta = self.client.post(formulario.redirect_chain[-1][0],
                                     {"new_password1": NUEVA, "new_password2": NUEVA}, follow=True)
        self.assertContains(respuesta, "Tu contraseña cambió")

        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(NUEVA))
        self.assertContains(self.client.get(enlace, follow=True), "Este enlace ya no sirve")
