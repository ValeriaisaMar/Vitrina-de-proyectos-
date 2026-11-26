"""Spec 010, historia 3: asistente para crear el primer admin."""

from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cuentas import configuracion_inicial as servicio
from cuentas.models import CambioRol, ConfiguracionInicial, Rol, RolAsignado, Usuario
from cuentas.roles import CLAVE_SESION
from cuentas.tests.utilidades import CLAVE, crear_usuario

PAGINA = reverse("configuracion_inicial")
PANEL = reverse("vitrina:panel")
ENTRAR = reverse("cuentas:entrar")
LOGGER = "cuentas.configuracion_inicial"
GENERICO = "El código o los datos de la cuenta no son válidos"
CLAVE_NUEVA = "Otra-clave-segura-456"


class Base(TestCase):
    def nuevo_codigo(self):
        with self.assertLogs(LOGGER, "WARNING"):
            return servicio.generar_codigo()

    def datos_nueva(self, codigo, **cambios):
        datos = {"opcion": "nueva", "codigo": servicio.formatear(codigo), "nombres": "Rosa", "apellidos": "Mera",
                 "email": "Rosa@Uteq.edu.ec", "password1": CLAVE_NUEVA, "password2": CLAVE_NUEVA}
        return {**datos, **cambios}

    def datos_existente(self, codigo, email="ana@correo.com", password=CLAVE):
        return {"opcion": "existente", "codigo": codigo, "email": email, "password": password}

    def enviar(self, datos):
        # Cualquier aviso del log queda capturado (no ensucia la salida de las pruebas)
        with self.assertLogs(LOGGER, "INFO") as registro:
            servicio.logger.info("prueba")
            respuesta = self.client.post(PAGINA, datos)
        self.log = "\n".join(registro.output)
        return respuesta

    def admins(self):
        return Usuario.objects.filter(is_active=True, roles_asignados__rol=Rol.ADMIN)


class AccesoTests(Base):
    def test_404_con_admin_activo(self):
        crear_usuario("admin@correo.com", rol="admin")
        self.assertEqual(self.client.get(PAGINA).status_code, 404)
        self.assertEqual(self.client.post(PAGINA, {"opcion": "nueva"}).status_code, 404)

    def test_con_sesion_pide_cerrarla_y_no_procesa(self):
        ana = crear_usuario()
        self.client.force_login(ana)
        respuesta = self.client.get(PAGINA)
        self.assertContains(respuesta, "primero cierra la sesión")
        self.assertContains(respuesta, reverse("cuentas:salir"))
        codigo = self.nuevo_codigo()
        self.client.post(PAGINA, self.datos_nueva(codigo))
        self.assertFalse(self.admins().exists())

    def test_asistente_muestra_pasos_ayuda_pestanas_y_volver(self):
        with self.assertLogs(LOGGER, "WARNING"):
            respuesta = self.client.get(PAGINA)
        for texto in ("Código de configuración", "Datos del admin", "¿Dónde encuentro el código?",
                      "docker compose exec web python manage.py codigo_configuracion_inicial",
                      "Crear una cuenta nueva", "Usar una cuenta que ya existe", "Volver a Entrar",
                      "sello-carrera"):
            self.assertContains(respuesta, texto)
        self.assertContains(respuesta, 'name="password2"')
        with self.assertNoLogs(LOGGER, "WARNING"):
            respuesta = self.client.get(PAGINA + "?opcion=existente")
        self.assertContains(respuesta, 'name="password"')
        self.assertNotContains(respuesta, 'name="password2"')


class CuentaNuevaTests(Base):
    def test_crea_el_admin_y_entra_al_panel(self):
        codigo = self.nuevo_codigo()
        respuesta = self.enviar(self.datos_nueva(codigo))
        self.assertRedirects(respuesta, PANEL, fetch_redirect_response=False)

        rosa = Usuario.objects.get(email="rosa@uteq.edu.ec")
        self.assertTrue(rosa.is_active)
        self.assertFalse(rosa.is_staff)
        self.assertEqual(rosa.roles, ["admin"])
        self.assertIsNone(RolAsignado.objects.get(usuario=rosa).asignado_por)
        cambio = CambioRol.objects.get(usuario=rosa)
        self.assertEqual((cambio.rol, cambio.accion, cambio.hecho_por, cambio.motivo),
                         ("admin", "agregado", None, "Configuración inicial"))
        self.assertEqual(mail.outbox, [])  # sin enlace de activación
        self.assertFalse(rosa.tiene_perfil_publico)  # solo admin: sin perfil público (spec 009)

        # Sesión iniciada con rol activo admin, mensaje y siguientes pasos (una sola vez)
        self.assertEqual(int(self.client.session["_auth_user_id"]), rosa.pk)
        self.assertEqual(self.client.session[CLAVE_SESION], "admin")
        panel = self.client.get(PANEL)
        self.assertContains(panel, "Listo. Ya eres administrador de la Vitrina.")
        self.assertContains(panel, "Siguientes pasos")
        for url in (reverse("cuentas:correo_envio"), reverse("proyectos:periodos"), reverse("proyectos:planes")):
            self.assertContains(panel, f'href="{url}"')
        self.assertNotContains(self.client.get(PANEL), "Siguientes pasos")

        # Log sin datos sensibles
        self.assertIn("Configuración inicial completada: admin rosa@uteq.edu.ec (cuenta nueva)", self.log)
        self.assertNotIn(CLAVE_NUEVA, self.log)
        self.assertNotIn(codigo, self.log)

        # La página ya no existe, el código se gastó y el enlace de Entrar desapareció
        self.assertEqual(self.client.get(PAGINA).status_code, 404)
        self.assertFalse(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))
        self.assertIsNotNone(ConfiguracionInicial.obtener().completada_en)
        self.client.logout()
        self.assertNotContains(self.client.get(ENTRAR), "¿Instalación nueva?")

    def test_correo_ya_registrado_con_codigo_correcto(self):
        crear_usuario("rosa@uteq.edu.ec")
        codigo = self.nuevo_codigo()
        respuesta = self.enviar(self.datos_nueva(codigo))
        self.assertContains(respuesta, "Ya hay una cuenta con este correo")
        self.assertFalse(self.admins().exists())
        self.assertTrue(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))  # no se gastó

    def test_correo_ya_registrado_con_codigo_malo_no_lo_revela(self):
        crear_usuario("rosa@uteq.edu.ec")
        self.nuevo_codigo()
        respuesta = self.enviar(self.datos_nueva("AAAABBBBCCCC"))
        self.assertContains(respuesta, GENERICO)
        self.assertNotContains(respuesta, "Ya hay una cuenta con este correo")

    def test_contrasena_debil_o_distinta(self):
        codigo = self.nuevo_codigo()
        respuesta = self.client.post(PAGINA, self.datos_nueva(codigo, password1="12345678", password2="12345678"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].errors)
        respuesta = self.client.post(PAGINA, self.datos_nueva(codigo, password2="otra-cosa-789"))
        self.assertIn("password2", respuesta.context["form"].errors)
        self.assertFalse(Usuario.objects.exists())


class CuentaExistenteTests(Base):
    def test_promueve_y_conserva_sus_roles(self):
        ana = crear_usuario("ana@correo.com", roles=["estudiante", "profesor"])
        codigo = self.nuevo_codigo()
        respuesta = self.enviar(self.datos_existente(codigo, email="ANA@correo.com"))
        self.assertRedirects(respuesta, PANEL, fetch_redirect_response=False)
        ana.olvidar_roles()
        self.assertEqual(ana.roles, ["estudiante", "profesor", "admin"])
        self.assertEqual(CambioRol.objects.get(usuario=ana).motivo, "Configuración inicial")
        self.assertEqual(self.client.session[CLAVE_SESION], "admin")
        self.assertIn("(cuenta existente)", self.log)
        self.assertNotIn(CLAVE, self.log)

    def test_cuenta_sin_activar_queda_activa(self):
        ana = crear_usuario("ana@correo.com", activo=False)
        codigo = self.nuevo_codigo()
        self.enviar(self.datos_existente(codigo))
        ana.refresh_from_db()
        self.assertTrue(ana.is_active)
        self.assertTrue(ana.tiene_rol(Rol.ADMIN))

    def test_mismo_mensaje_para_codigo_malo_contrasena_mala_y_correo_inexistente(self):
        crear_usuario("ana@correo.com")
        codigo = self.nuevo_codigo()
        casos = [
            self.datos_existente("AAAABBBBCCCC"),
            self.datos_existente(codigo, password="no-es-esta"),
            self.datos_existente(codigo, email="nadie@correo.com"),
        ]
        for datos in casos:
            respuesta = self.enviar(datos)
            self.assertContains(respuesta, GENERICO)
            self.assertNotIn(datos["password"], self.log)
        self.assertFalse(self.admins().exists())
        # Solo el código malo cuenta para invalidar el código
        self.assertEqual(ConfiguracionInicial.obtener().intentos_fallidos, 1)


class CodigoTests(Base):
    def test_codigo_vencido(self):
        crear_usuario("ana@correo.com")
        codigo = self.nuevo_codigo()
        luego = timezone.now() + timedelta(minutes=31)
        with mock.patch("django.utils.timezone.now", return_value=luego):
            respuesta = self.enviar(self.datos_existente(codigo))
        self.assertContains(respuesta, GENERICO)
        self.assertFalse(self.admins().exists())

    def test_codigo_usado_no_vuelve_a_servir(self):
        codigo = self.nuevo_codigo()
        self.enviar(self.datos_nueva(codigo))
        self.client.logout()
        Usuario.objects.update(is_active=False)  # se quedan sin admin (cambio directo en la base)
        crear_usuario("ana@correo.com")
        respuesta = self.enviar(self.datos_existente(codigo))
        self.assertContains(respuesta, GENERICO)
        self.assertFalse(self.admins().exists())

    def test_cinco_codigos_malos_invalidan_el_codigo(self):
        crear_usuario("ana@correo.com")
        codigo = self.nuevo_codigo()
        for _ in range(5):
            self.assertContains(self.enviar(self.datos_existente("AAAABBBBCCCC")), GENERICO)
        self.assertIn("tras 5 intentos fallidos", self.log)  # aviso WARNING en el log
        # Desde otra IP (sin bloqueo) y con el código correcto: ya no sirve, hay que generar otro
        with self.assertLogs(LOGGER, "INFO"):
            servicio.logger.info("prueba")
            respuesta = self.client.post(PAGINA, self.datos_existente(codigo), REMOTE_ADDR="10.0.0.2")
        self.assertContains(respuesta, GENERICO)
        self.assertFalse(self.admins().exists())

    def test_limite_de_intentos_por_ip(self):
        crear_usuario("ana@correo.com")
        codigo = self.nuevo_codigo()
        for _ in range(5):
            respuesta = self.enviar(self.datos_existente(codigo, password="no-es-esta"))
            self.assertContains(respuesta, GENERICO)
        respuesta = self.client.post(PAGINA, self.datos_existente(codigo))  # ahora con la contraseña buena
        self.assertContains(respuesta, "Demasiados intentos fallidos")
        self.assertFalse(self.admins().exists())


class ServicioTests(Base):
    def test_dos_envios_crean_un_solo_admin(self):
        crear_usuario("ana@correo.com")
        codigo = self.nuevo_codigo()
        datos = {"email": "ana@correo.com", "password": CLAVE}
        with self.assertLogs(LOGGER, "INFO"):
            servicio.crear_primer_admin(codigo, "existente", datos)
        with self.assertRaises(servicio.ConfiguracionNoDisponible):
            servicio.crear_primer_admin(codigo, "nueva", {"email": "otra@correo.com", "password1": CLAVE_NUEVA,
                                                          "nombres": "Otra", "apellidos": "Persona"})
        self.assertEqual(self.admins().count(), 1)
        self.assertFalse(Usuario.objects.filter(email="otra@correo.com").exists())

    def test_usa_un_bloqueo_de_fila(self):
        """La creación bloquea la fila de ConfiguracionInicial (select_for_update) dentro de la transacción."""
        codigo = self.nuevo_codigo()
        with mock.patch.object(ConfiguracionInicial.objects, "select_for_update",
                               wraps=ConfiguracionInicial.objects.select_for_update) as bloqueo:
            with self.assertRaises(servicio.DatosInvalidos):
                servicio.crear_primer_admin("AAAABBBBCCCC", "existente", {"email": "x@correo.com", "password": "x"})
        bloqueo.assert_called_once()
        self.assertTrue(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))
        self.assertEqual(ConfiguracionInicial.obtener().intentos_fallidos, 1)  # el fallo no se deshizo


class CreateSuperuserTests(Base):
    def test_deja_el_motivo_e_invalida_el_codigo_y_la_cache(self):
        codigo = self.nuevo_codigo()
        self.assertContains(self.client.get(ENTRAR), "¿Instalación nueva?")
        admin = Usuario.objects.create_superuser("root@correo.com", "clave-segura-123", nombres="R", apellidos="S")
        self.assertEqual(CambioRol.objects.get(usuario=admin).motivo, "Configuración inicial")
        self.assertFalse(servicio.codigo_correcto(ConfiguracionInicial.obtener(), codigo))
        self.assertNotContains(self.client.get(ENTRAR), "¿Instalación nueva?")
        self.assertEqual(self.client.get(PAGINA).status_code, 404)
