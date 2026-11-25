"""Historia 1: registro con correo real y activación por enlace."""

from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import CLAVE, Usuario, crear_usuario, enlace_en_correo

DATOS = {
    "nombres": "Valeria", "apellidos": "Martínez", "email": "Valeria@Correo.com",
    "password1": CLAVE, "password2": CLAVE,
}


class RegistroTests(TestCase):
    def registrar(self, **cambios):
        return self.client.post(reverse("cuentas:registro"), {**DATOS, **cambios})

    def test_crea_cuenta_inactiva_de_estudiante_y_envia_el_enlace(self):
        respuesta = self.registrar()
        self.assertRedirects(respuesta, reverse("cuentas:revisa_correo"))

        usuario = Usuario.objects.get(email="valeria@correo.com")
        self.assertFalse(usuario.is_active)
        self.assertEqual(usuario.roles, [Rol.ESTUDIANTE])  # solo estudiante

        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ["valeria@correo.com"])
        self.assertIn("/cuentas/activar/", correo.body)
        self.assertEqual(len(correo.alternatives), 1)  # versión HTML

    def test_la_pagina_revisa_tu_correo_muestra_la_direccion(self):
        respuesta = self.client.post(reverse("cuentas:registro"), DATOS, follow=True)
        self.assertContains(respuesta, "valeria@correo.com")
        self.assertContains(respuesta, "24 horas")

    def test_rechaza_correo_repetido_sin_importar_mayusculas(self):
        crear_usuario(email="valeria@correo.com")
        respuesta = self.registrar(email="VALERIA@correo.COM")
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ya existe una cuenta con este correo")
        self.assertEqual(Usuario.objects.count(), 1)

    def test_rechaza_contrasenas_distintas(self):
        respuesta = self.registrar(password2="otra-clave-distinta-9")
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_rechaza_contrasena_debil(self):
        respuesta = self.registrar(password1="12345678", password2="12345678")
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.exists())

    def test_campos_obligatorios(self):
        respuesta = self.registrar(nombres="", apellidos="")
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.exists())

    def test_con_sesion_iniciada_no_muestra_el_registro(self):
        self.client.force_login(crear_usuario())
        self.assertRedirects(self.client.get(reverse("cuentas:registro")), reverse("vitrina:inicio"))

    def test_si_el_correo_falla_la_cuenta_se_crea_igual_y_se_avisa(self):
        with mock.patch("cuentas.correos.EmailMultiAlternatives.send", side_effect=OSError("sin red")):
            respuesta = self.client.post(reverse("cuentas:registro"), DATOS, follow=True)
        self.assertTrue(Usuario.objects.filter(email="valeria@correo.com").exists())
        self.assertContains(respuesta, "no pudimos enviar el correo")


class ActivacionTests(TestCase):
    def setUp(self):
        self.client.post(reverse("cuentas:registro"), DATOS)
        self.enlace = enlace_en_correo(mail.outbox[0])
        self.usuario = Usuario.objects.get(email="valeria@correo.com")

    def test_enlace_valido_activa_e_inicia_sesion(self):
        respuesta = self.client.get(self.enlace, follow=True)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_active)
        self.assertTrue(respuesta.context["user"].is_authenticated)
        self.assertContains(respuesta, "Tu cuenta está activa")

    def test_el_enlace_sirve_una_sola_vez(self):
        self.client.get(self.enlace)
        self.client.logout()
        respuesta = self.client.get(self.enlace)
        self.assertEqual(respuesta.status_code, 400)
        self.assertContains(respuesta, "Este enlace ya no sirve", status_code=400)

    def test_enlace_alterado_no_sirve(self):
        respuesta = self.client.get(self.enlace[:-3] + "xyz/")
        self.assertEqual(respuesta.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_active)

    def test_uid_invalido_no_rompe_la_pagina(self):
        respuesta = self.client.get(reverse("cuentas:activar", args=["no-es-base64", "token"]))
        self.assertEqual(respuesta.status_code, 400)

    def test_el_enlace_vence(self):
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):  # simula que ya pasó el plazo
            respuesta = self.client.get(self.enlace)
        self.assertEqual(respuesta.status_code, 400)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_active)


class ReenvioTests(TestCase):
    def test_reenvia_a_cuenta_inactiva(self):
        crear_usuario(email="pendiente@correo.com", activo=False)
        respuesta = self.client.post(reverse("cuentas:reenviar"), {"email": "Pendiente@correo.com"}, follow=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertContains(respuesta, "pendiente@correo.com")

    def test_responde_igual_si_el_correo_no_existe_o_ya_esta_activo(self):
        crear_usuario(email="activa@correo.com", activo=True)
        r1 = self.client.post(reverse("cuentas:reenviar"), {"email": "nadie@correo.com"}, follow=True)
        r2 = self.client.post(reverse("cuentas:reenviar"), {"email": "activa@correo.com"}, follow=True)
        self.assertEqual(len(mail.outbox), 0)
        for respuesta in (r1, r2):
            self.assertContains(respuesta, "Si hay una cuenta pendiente de activar")


class IdiomaCuentasTests(TestCase):
    def test_registro_y_correo_en_ingles(self):
        self.client.cookies["django_language"] = "en"
        self.assertContains(self.client.get(reverse("cuentas:registro")), "Create your account")
        self.client.post(reverse("cuentas:registro"), DATOS)
        self.assertEqual(mail.outbox[0].subject, "Activate your Project Showcase account")
        self.assertIn("The link expires in 24 hours", mail.outbox[0].body)
