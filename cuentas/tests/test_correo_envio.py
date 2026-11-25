"""Spec 008, historia 3: el admin configura desde la app el correo que envía los mensajes.

Ninguna prueba usa un servidor SMTP real: se usa el backend en memoria (locmem) y mocks.
"""

import smtplib
import socket
import ssl
from unittest import mock

from cryptography.fernet import Fernet
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.test import TestCase, override_settings
from django.urls import reverse

from config.correo import CorreoConfigurableBackend
from cuentas import cifrado
from cuentas.correo_envio import mensaje_de_error
from cuentas.models import ConfiguracionCorreo, Rol
from cuentas.tests.utilidades import crear_usuario

CLAVE_PRUEBA = Fernet.generate_key().decode()
URL = reverse("cuentas:correo_envio")
LOCMEM = {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
CONFIGURABLE = {"default": {"BACKEND": "config.correo.CorreoConfigurableBackend", "OPTIONS": {"respaldo": LOCMEM}}}
SMTP_ENVIAR = "django.core.mail.backends.smtp.EmailBackend.send_messages"

DATOS = {
    "servidor": "smtp.gmail.com", "puerto": 587, "seguridad": "starttls",
    "usuario": "vitrina@gmail.com", "clave": "abcd efgh ijkl mnop",
    "nombre_remitente": "Vitrina de Proyectos UTEQ", "correo_remitente": "",
}


@override_settings(CLAVE_CIFRADO=CLAVE_PRUEBA)
class CifradoTests(TestCase):
    def test_cifra_y_descifra(self):
        cifrada = cifrado.cifrar("secreta123")
        self.assertNotIn("secreta123", cifrada)
        self.assertEqual(cifrado.descifrar(cifrada), "secreta123")

    def test_con_otra_clave_no_se_puede_leer(self):
        cifrada = cifrado.cifrar("secreta123")
        with override_settings(CLAVE_CIFRADO=Fernet.generate_key().decode()), self.assertRaises(cifrado.ClaveIlegible):
            cifrado.descifrar(cifrada)

    @override_settings(CLAVE_CIFRADO="")
    def test_sin_clave_de_cifrado_avisa_que_falta(self):
        self.assertFalse(cifrado.hay_clave())
        with self.assertRaisesMessage(ImproperlyConfigured, "CLAVE_CIFRADO"):
            cifrado.cifrar("x")


@override_settings(CLAVE_CIFRADO=CLAVE_PRUEBA)
class PaginaCorreoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = crear_usuario("admin@uteq.edu.ec", rol=Rol.ADMIN)
        self.client.force_login(self.admin)

    def test_solo_el_admin_activo(self):
        for rol in (Rol.ESTUDIANTE, Rol.PROFESOR):
            self.client.force_login(crear_usuario(f"{rol}@correo.com", rol=rol))
            self.assertEqual(self.client.get(URL).status_code, 403)
            self.assertEqual(self.client.post(URL, {**DATOS, "accion": "guardar"}).status_code, 403)
        self.assertFalse(ConfiguracionCorreo.objects.exists())

    def test_guardar_cifra_la_contrasena_y_nunca_la_muestra(self):
        respuesta = self.client.post(URL, {**DATOS, "accion": "guardar"})
        self.assertRedirects(respuesta, URL, fetch_redirect_response=False)
        configuracion = ConfiguracionCorreo.actual()
        self.assertNotIn("abcdefghijklmnop", configuracion.clave_cifrada)
        self.assertEqual(cifrado.descifrar(configuracion.clave_cifrada), "abcdefghijklmnop")  # sin espacios
        self.assertEqual(configuracion.actualizado_por, self.admin)
        pagina = self.client.get(URL)
        self.assertContains(pagina, "Contraseña guardada")
        self.assertNotContains(pagina, "abcdefghijklmnop")
        self.assertNotContains(pagina, configuracion.clave_cifrada)

    def test_dejar_la_contrasena_vacia_conserva_la_anterior(self):
        self.client.post(URL, {**DATOS, "accion": "guardar"})
        self.client.post(URL, {**DATOS, "clave": "", "servidor": "smtp.office365.com", "accion": "guardar"})
        configuracion = ConfiguracionCorreo.actual()
        self.assertEqual(configuracion.servidor, "smtp.office365.com")
        self.assertEqual(cifrado.descifrar(configuracion.clave_cifrada), "abcdefghijklmnop")

    def test_la_primera_vez_la_contrasena_es_obligatoria(self):
        respuesta = self.client.post(URL, {**DATOS, "clave": "", "accion": "guardar"})
        self.assertContains(respuesta, "Escribe la contraseña de aplicación")

    @override_settings(CLAVE_CIFRADO="")
    def test_sin_clave_de_cifrado_no_guarda_la_contrasena(self):
        respuesta = self.client.post(URL, {**DATOS, "accion": "guardar"})
        self.assertContains(respuesta, "CLAVE_CIFRADO")
        self.assertFalse(ConfiguracionCorreo.objects.exists())

    def test_configuracion_rapida_sin_javascript(self):
        respuesta = self.client.get(URL, {"proveedor": "outlook"})
        self.assertEqual(respuesta.context["form"].initial["servidor"], "smtp.office365.com")

    def test_probar_envia_al_admin_sin_guardar(self):
        with mock.patch(SMTP_ENVIAR, return_value=1) as enviar:
            respuesta = self.client.post(URL, {**DATOS, "accion": "probar"})
        self.assertContains(respuesta, "Enviamos un correo de prueba a admin@uteq.edu.ec")
        mensaje = enviar.call_args.args[0][0]
        self.assertEqual(mensaje.to, ["admin@uteq.edu.ec"])
        self.assertIn("vitrina@gmail.com", mensaje.from_email)
        self.assertFalse(ConfiguracionCorreo.objects.exists())  # probar no guarda

    def test_probar_explica_los_errores(self):
        casos = [
            (smtplib.SMTPAuthenticationError(535, b"bad"), "rechazó el usuario o la contraseña"),
            (socket.timeout(), "no responden"),
            (ConnectionRefusedError(), "no responden"),
            (ssl.SSLError("bad"), "conexión segura"),
        ]
        for error, texto in casos:
            cache.clear()
            with self.subTest(error=type(error).__name__), mock.patch(SMTP_ENVIAR, side_effect=error):
                self.assertContains(self.client.post(URL, {**DATOS, "accion": "probar"}), texto)

    def test_la_prueba_queda_en_la_tarjeta_de_estado(self):
        self.client.post(URL, {**DATOS, "accion": "guardar"})
        with mock.patch(SMTP_ENVIAR, side_effect=smtplib.SMTPAuthenticationError(535, b"bad")):
            self.client.post(URL, {**DATOS, "clave": "", "accion": "probar"})  # vacía: usa la guardada
        configuracion = ConfiguracionCorreo.actual()
        self.assertIs(configuracion.ultima_prueba_ok, False)
        self.assertContains(self.client.get(URL), "Falló")

    def test_probar_tiene_limite_de_intentos(self):
        with mock.patch(SMTP_ENVIAR, return_value=1) as enviar:
            for _ in range(7):
                respuesta = self.client.post(URL, {**DATOS, "accion": "probar"})
        self.assertEqual(enviar.call_count, 5)
        self.assertContains(respuesta, "Hiciste varias pruebas seguidas")

    def test_mensaje_generico_para_errores_desconocidos(self):
        self.assertIn("No se pudo", mensaje_de_error(ValueError("x")))


@override_settings(CLAVE_CIFRADO=CLAVE_PRUEBA, MAILERS=CONFIGURABLE)
class BackendConfigurableTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_sin_configuracion_usa_el_respaldo_del_env(self):
        EmailMessage("Hola", "Cuerpo", to=["ana@correo.com"]).send()
        self.assertEqual(len(mail.outbox), 1)  # salió por el respaldo (en memoria)

    def test_con_configuracion_usa_smtp_y_el_remitente_configurado(self):
        ConfiguracionCorreo(
            servidor="smtp.office365.com", puerto=587, seguridad="starttls", usuario="vitrina@uteq.edu.ec",
            clave_cifrada=cifrado.cifrar("clave"), nombre_remitente="Vitrina UTEQ",
        ).save()
        with mock.patch(SMTP_ENVIAR, return_value=1) as enviar:
            EmailMessage("Hola", "Cuerpo", to=["ana@correo.com"]).send()
        self.assertEqual(len(mail.outbox), 0)
        backend = enviar.call_args  # send_messages(self, mensajes) se llamó sobre el backend SMTP
        mensaje = backend.args[0][0]
        self.assertEqual(mensaje.from_email, "Vitrina UTEQ <vitrina@uteq.edu.ec>")

    def test_al_guardar_se_invalida_la_cache(self):
        EmailMessage("Uno", "Cuerpo", to=["a@b.com"]).send()  # deja en caché "sin configuración"
        ConfiguracionCorreo(servidor="smtp.gmail.com", usuario="v@gmail.com", clave_cifrada=cifrado.cifrar("c")).save()
        with mock.patch(SMTP_ENVIAR, return_value=1) as enviar:
            EmailMessage("Dos", "Cuerpo", to=["a@b.com"]).send()
        self.assertTrue(enviar.called)

    def test_si_la_contrasena_no_se_puede_leer_usa_el_respaldo(self):
        ConfiguracionCorreo(servidor="smtp.gmail.com", usuario="v@gmail.com", clave_cifrada="basura").save()
        EmailMessage("Hola", "Cuerpo", to=["a@b.com"]).send()
        self.assertEqual(len(mail.outbox), 1)

    def test_el_backend_smtp_recibe_los_datos(self):
        ConfiguracionCorreo(servidor="smtp.ejemplo.com", puerto=465, seguridad="ssl", usuario="v@ejemplo.com",
                            clave_cifrada=cifrado.cifrar("c")).save()
        backend, remitente = CorreoConfigurableBackend(alias="default", respaldo=LOCMEM)._elegir()
        self.assertEqual((backend.host, backend.port, backend.use_ssl, backend.use_tls, backend.password),
                         ("smtp.ejemplo.com", 465, True, False, "c"))
        self.assertIn("v@ejemplo.com", remitente)

    def test_la_configuracion_no_aparece_en_el_admin_de_django(self):
        from django.contrib import admin

        self.assertNotIn(ConfiguracionCorreo, admin.site._registry)
