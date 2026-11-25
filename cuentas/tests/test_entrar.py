"""Historia 2: iniciar y cerrar sesión con límite de intentos."""

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from cuentas import limite
from cuentas.tests.utilidades import CLAVE, crear_usuario


class EntrarTests(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = crear_usuario(email="ana@correo.com")
        self.url = reverse("cuentas:entrar")

    def entrar(self, email="ana@correo.com", clave=CLAVE, **extra):
        return self.client.post(self.url, {"username": email, "password": clave, **extra})

    def test_entra_con_el_correo_en_cualquier_mayuscula(self):
        respuesta = self.entrar(email="ANA@Correo.com")
        self.assertRedirects(respuesta, reverse("vitrina:panel"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.usuario.pk)

    def test_vuelve_a_la_pagina_de_la_que_venia(self):
        respuesta = self.entrar(next=reverse("cuentas:perfil"))
        self.assertRedirects(respuesta, reverse("cuentas:perfil"))

    def test_ignora_un_next_de_otro_sitio(self):
        respuesta = self.entrar(next="https://sitio-malicioso.com/")
        self.assertRedirects(respuesta, reverse("vitrina:panel"))

    def test_datos_incorrectos_dan_un_mensaje_que_no_revela_la_cuenta(self):
        r1 = self.entrar(clave="mala-clave")
        r2 = self.entrar(email="nadie@correo.com")
        for respuesta in (r1, r2):
            self.assertContains(respuesta, "El correo o la contraseña no son correctos.")

    def test_cuenta_inactiva_con_clave_correcta_invita_a_activar(self):
        crear_usuario(email="nueva@correo.com", activo=False)
        respuesta = self.entrar(email="nueva@correo.com")
        self.assertContains(respuesta, "Tu cuenta aún no está activa")
        self.assertContains(respuesta, reverse("cuentas:reenviar"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_bloquea_tras_cinco_fallos_aunque_la_clave_sea_correcta(self):
        for _ in range(limite.MAXIMO_INTENTOS):
            self.entrar(clave="mala-clave")
        respuesta = self.entrar()
        self.assertContains(respuesta, "Demasiados intentos fallidos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_el_bloqueo_es_por_correo(self):
        for _ in range(limite.MAXIMO_INTENTOS):
            self.entrar(email="otra@correo.com", clave="mala-clave")
        self.assertRedirects(self.entrar(), reverse("vitrina:panel"))

    def test_un_acierto_reinicia_el_conteo(self):
        for _ in range(limite.MAXIMO_INTENTOS - 1):
            self.entrar(clave="mala-clave")
        self.entrar()
        self.client.logout()
        self.entrar(clave="mala-clave")
        self.assertRedirects(self.entrar(), reverse("vitrina:panel"))

    def test_sin_recordar_la_sesion_termina_al_cerrar_el_navegador(self):
        self.entrar()
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_recordar_mantiene_la_sesion(self):
        self.entrar(recordar="on")
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_con_sesion_iniciada_no_muestra_el_formulario(self):
        self.client.force_login(self.usuario)
        self.assertRedirects(self.client.get(self.url), reverse("vitrina:panel"))


class SalirTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario())

    def test_salir_por_post_cierra_la_sesion(self):
        respuesta = self.client.post(reverse("cuentas:salir"))
        self.assertRedirects(respuesta, reverse("vitrina:inicio"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_salir_por_get_no_funciona(self):
        self.assertEqual(self.client.get(reverse("cuentas:salir")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_el_encabezado_muestra_perfil_y_salir(self):
        respuesta = self.client.get(reverse("vitrina:inicio"))
        self.assertContains(respuesta, "Hola, Ana")
        self.assertContains(respuesta, reverse("cuentas:salir"))
        self.assertContains(respuesta, reverse("cuentas:perfil"))
