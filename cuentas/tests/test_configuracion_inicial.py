"""Spec 010, historias 1 y 2: código de configuración inicial, logs por consola y enlace en Entrar."""

import logging
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cuentas import configuracion_inicial as servicio
from cuentas.models import ConfiguracionInicial
from cuentas.tests.utilidades import crear_usuario

PAGINA = reverse("configuracion_inicial")
ENTRAR = reverse("cuentas:entrar")
LOGGER = "cuentas.configuracion_inicial"


def codigo_del_bloque(texto):
    """Saca el código («XXXX-XXXX-XXXX») del bloque impreso."""
    linea = next(l for l in texto.splitlines() if l.startswith("Código: "))
    return linea.split()[1]


class CodigoTests(TestCase):
    def test_formato_y_alfabeto_sin_caracteres_confusos(self):
        with self.assertLogs(LOGGER, "WARNING"):
            codigo = servicio.generar_codigo()
        self.assertEqual(len(codigo), 12)
        self.assertTrue(set(codigo) <= set(servicio.ALFABETO))
        for confuso in "0O1IL":
            self.assertNotIn(confuso, servicio.ALFABETO)
        self.assertRegex(servicio.formatear(codigo), r"^[A-Z2-9]{4}-[A-Z2-9]{4}-[A-Z2-9]{4}$")

    def test_solo_se_guarda_la_huella(self):
        with self.assertLogs(LOGGER, "WARNING"):
            codigo = servicio.generar_codigo()
        configuracion = ConfiguracionInicial.obtener()
        self.assertEqual(len(configuracion.hash_codigo), 64)
        self.assertNotIn(codigo, configuracion.hash_codigo)
        self.assertTrue(servicio.codigo_correcto(configuracion, codigo))

    def test_ignora_guiones_espacios_y_minusculas(self):
        with self.assertLogs(LOGGER, "WARNING"):
            codigo = servicio.generar_codigo()
        escrito = " " + servicio.formatear(codigo).lower().replace("-", " - ") + " "
        self.assertTrue(servicio.codigo_correcto(ConfiguracionInicial.obtener(), escrito))
        self.assertFalse(servicio.codigo_correcto(ConfiguracionInicial.obtener(), "AAAA-BBBB-CCCC"))
        self.assertFalse(servicio.codigo_correcto(ConfiguracionInicial.obtener(), ""))

    def test_vence_a_los_30_minutos(self):
        with self.assertLogs(LOGGER, "WARNING"):
            codigo = servicio.generar_codigo()
        configuracion = ConfiguracionInicial.obtener()
        self.assertEqual(configuracion.vence_en - configuracion.creado_en, timedelta(minutes=30))
        luego = timezone.now() + timedelta(minutes=31)
        with mock.patch("django.utils.timezone.now", return_value=luego):
            self.assertFalse(servicio.codigo_correcto(configuracion, codigo))

    def test_cinco_fallos_invalidan_el_codigo_y_avisan(self):
        with self.assertLogs(LOGGER, "WARNING"):
            codigo = servicio.generar_codigo()
        configuracion = ConfiguracionInicial.obtener()
        for _ in range(4):
            servicio.registrar_fallo(configuracion)
        self.assertTrue(servicio.codigo_correcto(configuracion, codigo))
        with self.assertLogs(LOGGER, "WARNING") as registro:
            servicio.registrar_fallo(configuracion)
        self.assertIn("5 intentos fallidos", registro.output[0])
        self.assertNotIn(codigo, registro.output[0])
        self.assertFalse(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))

    def test_invalidar_lo_deja_sin_uso(self):
        with self.assertLogs(LOGGER, "WARNING"):
            codigo = servicio.generar_codigo()
        servicio.invalidar_codigo(completada=True)
        configuracion = ConfiguracionInicial.obtener()
        self.assertFalse(servicio.codigo_correcto(configuracion, codigo))
        self.assertIsNotNone(configuracion.completada_en)

    def test_asegurar_no_reemplaza_un_codigo_vigente(self):
        with self.assertLogs(LOGGER, "WARNING"):
            codigo = servicio.generar_codigo()
        self.assertFalse(servicio.asegurar_codigo())
        self.assertTrue(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))

    def test_hay_admin_activo(self):
        self.assertFalse(servicio.hay_admin_activo())
        crear_usuario("inactivo@correo.com", activo=False, rol="admin")
        crear_usuario("profe@correo.com", rol="profesor")
        self.assertFalse(servicio.hay_admin_activo())
        crear_usuario("admin@correo.com", rol="admin")
        self.assertTrue(servicio.hay_admin_activo())


class ComandoTests(TestCase):
    def correr(self):
        salida = StringIO()
        with self.assertLogs(LOGGER, "WARNING") as registro:
            call_command("codigo_configuracion_inicial", stdout=salida)
        return salida.getvalue(), registro.output

    def test_imprime_el_bloque_en_la_terminal(self):
        salida, log = self.correr()
        self.assertIn("==== VITRINA: CÓDIGO DE CONFIGURACIÓN INICIAL ====", salida)
        self.assertIn("(vence en 30 minutos)", salida)
        self.assertIn("Ábrelo en: /configuracion-inicial/", salida)
        codigo = codigo_del_bloque(salida)
        self.assertTrue(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))
        # En el log queda el aviso, pero no el código (no se repite en pantalla)
        self.assertNotIn(codigo, "".join(log))

    @override_settings(SITIO_URL="https://vitrina.ejemplo")
    def test_usa_la_url_del_sitio(self):
        salida, _log = self.correr()
        self.assertIn("Ábrelo en: https://vitrina.ejemplo/configuracion-inicial/", salida)

    def test_el_codigo_anterior_deja_de_servir(self):
        primero = codigo_del_bloque(self.correr()[0])
        segundo = codigo_del_bloque(self.correr()[0])
        configuracion = ConfiguracionInicial.obtener()
        self.assertFalse(servicio.codigo_correcto(configuracion, primero))
        self.assertTrue(servicio.codigo_correcto(configuracion, segundo))

    def test_falla_si_ya_hay_admin(self):
        crear_usuario("admin@correo.com", rol="admin")
        salida = StringIO()
        with self.assertRaisesMessage(CommandError, "Ya existe un administrador activo"):
            call_command("codigo_configuracion_inicial", stdout=salida)
        self.assertEqual(salida.getvalue(), "")
        self.assertFalse(ConfiguracionInicial.objects.exclude(hash_codigo="").exists())


class PaginaRespaldoTests(TestCase):
    def test_abrir_la_pagina_escribe_el_codigo_en_el_log_y_no_en_el_html(self):
        with self.assertLogs(LOGGER, "WARNING") as registro:
            respuesta = self.client.get(PAGINA)
        self.assertEqual(respuesta.status_code, 200)
        codigo = codigo_del_bloque(registro.output[0].split("\n", 1)[1])
        self.assertTrue(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))
        html = respuesta.content.decode()
        self.assertNotIn(codigo, html)
        self.assertNotIn(servicio.normalizar(codigo), html)
        self.assertIn("codigo_configuracion_inicial", html)

    def test_recargar_no_genera_otro(self):
        with self.assertLogs(LOGGER, "WARNING"):
            self.client.get(PAGINA)
        with self.assertNoLogs(LOGGER, "WARNING"):
            self.client.get(PAGINA)

    def test_404_si_hay_admin(self):
        crear_usuario("admin@correo.com", rol="admin")
        self.assertEqual(self.client.get(PAGINA).status_code, 404)
        self.assertEqual(self.client.post(PAGINA).status_code, 404)


class LoggingTests(TestCase):
    def test_configuracion_de_logging(self):
        config = settings.LOGGING
        self.assertFalse(config["disable_existing_loggers"])
        consola = config["handlers"]["consola"]
        self.assertEqual(consola["class"], "logging.StreamHandler")
        self.assertNotIn("require_debug_true", consola.get("filters", []))
        self.assertIn("{asctime} {levelname} {name}", config["formatters"][consola["formatter"]]["format"])
        cuentas = config["loggers"]["cuentas"]
        self.assertEqual((cuentas["handlers"], cuentas["level"], cuentas["propagate"]), (["consola"], "INFO", False))
        self.assertIn("consola", config["loggers"]["django"]["handlers"])
        self.assertEqual(config["loggers"]["django"]["level"], settings.NIVEL_LOG_DJANGO)

    @override_settings(DEBUG=False)
    def test_con_debug_false_el_bloque_sale_por_la_consola(self):
        """El logger de la configuración inicial usa el StreamHandler "consola" (no depende de DEBUG)."""
        logger = logging.getLogger("cuentas")
        consolas = [h for h in logger.handlers if type(h) is logging.StreamHandler]
        self.assertTrue(consolas, "El logger 'cuentas' no tiene el handler de consola")
        consola = consolas[0]
        flujo = StringIO()
        anterior = consola.setStream(flujo)
        try:
            servicio.generar_codigo()
        finally:
            consola.setStream(anterior)
        texto = flujo.getvalue()
        self.assertIn("WARNING cuentas.configuracion_inicial", texto)
        self.assertIn("==== VITRINA: CÓDIGO DE CONFIGURACIÓN INICIAL ====", texto)


class EnlaceEntrarTests(TestCase):
    """Historia 2: enlace discreto en Entrar, solo mientras no hay admin activo."""

    TEXTO = "¿Instalación nueva? Configurar la administración"

    def test_aparece_sin_admin(self):
        respuesta = self.client.get(ENTRAR)
        self.assertContains(respuesta, self.TEXTO)
        self.assertContains(respuesta, f'href="{PAGINA}"')

    def test_no_aparece_con_admin(self):
        crear_usuario("admin@correo.com", rol="admin")
        self.assertNotContains(self.client.get(ENTRAR), self.TEXTO)

    def test_desaparece_en_cuanto_hay_admin_y_vuelve_al_desactivarlo(self):
        from cuentas.roles import dar_rol

        self.assertContains(self.client.get(ENTRAR), self.TEXTO)  # queda guardado en la caché
        ana = crear_usuario("ana@correo.com")
        self.assertContains(self.client.get(ENTRAR), self.TEXTO)
        dar_rol(ana, "admin")
        self.assertNotContains(self.client.get(ENTRAR), self.TEXTO)
        ana.is_active = False
        ana.save()
        self.assertContains(self.client.get(ENTRAR), self.TEXTO)
        ana.is_active = True
        ana.save()
        self.assertNotContains(self.client.get(ENTRAR), self.TEXTO)
        ana.delete()
        self.assertContains(self.client.get(ENTRAR), self.TEXTO)

    def test_no_aparece_en_otras_paginas(self):
        for url in (reverse("cuentas:registro"), reverse("vitrina:inicio"), reverse("vitrina:explorar"),
                    reverse("cuentas:recuperar")):
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200, url)
            self.assertNotContains(respuesta, self.TEXTO)
            self.assertNotContains(respuesta, PAGINA)

    def test_no_consulta_la_base_en_cada_visita(self):
        self.client.get(ENTRAR)
        with mock.patch.object(servicio, "hay_admin_activo", wraps=servicio.hay_admin_activo) as consulta:
            self.client.get(ENTRAR)
            self.client.get(ENTRAR)
        consulta.assert_not_called()

    def test_la_cache_vence_sola(self):
        """Cambios que no pasan por señales (por ejemplo, directo en la base) se notan al vencer."""
        from cuentas.models import Usuario

        crear_usuario("admin@correo.com", rol="admin")
        self.assertNotContains(self.client.get(ENTRAR), self.TEXTO)
        Usuario.objects.update(is_active=False)  # update() no dispara señales
        self.assertNotContains(self.client.get(ENTRAR), self.TEXTO)
        servicio.olvidar_cache()  # equivale a que pasen los 60 segundos
        self.assertContains(self.client.get(ENTRAR), self.TEXTO)
        self.assertEqual(servicio.SEGUNDOS_CACHE, 60)
