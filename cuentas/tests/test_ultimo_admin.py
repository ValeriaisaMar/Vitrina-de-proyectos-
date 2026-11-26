"""Spec 010, historia 4: no quedarse sin admin y qué pasa si aun así ocurre."""

from django.test import TestCase
from django.urls import reverse

from cuentas import configuracion_inicial as servicio
from cuentas.models import ConfiguracionInicial, Rol, Usuario
from cuentas.tests.utilidades import CLAVE, crear_usuario

PAGINA = reverse("configuracion_inicial")
ENTRAR = reverse("cuentas:entrar")
LOGGER = "cuentas.configuracion_inicial"


class EnLaAppTests(TestCase):
    def test_no_se_puede_desactivar_al_ultimo_admin(self):
        """Aunque la vista ya impide desactivarse a uno mismo, el formulario también lo valida."""
        from cuentas.forms import FormularioGestionUsuario

        ana = crear_usuario("ana@correo.com", rol="admin")
        otro_editor = crear_usuario("profe@correo.com", rol="profesor")  # editor que no es ella
        form = FormularioGestionUsuario({"roles": ["admin"]}, instance=ana, editor=otro_editor)
        self.assertFalse(form.is_valid())
        self.assertIn("única cuenta admin activa", str(form.errors))
        ana.refresh_from_db()
        self.assertTrue(ana.is_active)

    def test_con_dos_admins_si_se_puede_desactivar_a_uno(self):
        ana = crear_usuario("ana@correo.com", rol="admin")
        beto = crear_usuario("beto@correo.com", rol="admin")
        self.client.force_login(ana)
        respuesta = self.client.post(reverse("cuentas:usuario_editar", args=[beto.pk]), {"roles": ["admin"]})
        self.assertEqual(respuesta.status_code, 302)
        beto.refresh_from_db()
        self.assertFalse(beto.is_active)


class EnElAdminDeDjangoTests(TestCase):
    """Un superusuario técnico (sin rol admin de la app) intenta dejar la plataforma sin admins."""

    def setUp(self):
        self.root = Usuario.objects.create_superuser("root@correo.com", "clave-segura-123", nombres="R", apellidos="S",
                                                    roles=["estudiante"])
        self.ana = crear_usuario("ana@correo.com", rol="admin")
        self.client.force_login(self.root)
        self.editar = reverse("admin:cuentas_usuario_change", args=[self.ana.pk])

    def datos(self, activo=True, rol=Rol.ADMIN, borrar_rol=False):
        fila = self.ana.roles_asignados.get()
        datos = {
            "email": self.ana.email, "nombres": "Ana", "apellidos": "Pérez",
            "fecha_registro_0": "2026-11-23", "fecha_registro_1": "10:00:00",
            "roles_asignados-TOTAL_FORMS": "1", "roles_asignados-INITIAL_FORMS": "1",
            "roles_asignados-MIN_NUM_FORMS": "0", "roles_asignados-MAX_NUM_FORMS": "1000",
            "roles_asignados-0-id": str(fila.pk), "roles_asignados-0-usuario": str(self.ana.pk),
            "roles_asignados-0-rol": rol,
        }
        if activo:
            datos["is_active"] = "on"
        if borrar_rol:
            datos["roles_asignados-0-DELETE"] = "on"
        return datos

    def test_no_se_puede_desactivar(self):
        respuesta = self.client.post(self.editar, self.datos(activo=False))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "única cuenta admin activa")
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.is_active)

    def test_no_se_puede_quitar_ni_cambiar_el_rol_admin(self):
        for datos in (self.datos(borrar_rol=True), self.datos(rol=Rol.PROFESOR)):
            respuesta = self.client.post(self.editar, datos)
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, "única cuenta admin activa")
        self.ana.olvidar_roles()
        self.assertEqual(self.ana.roles, ["admin"])

    def test_no_se_puede_eliminar_desde_su_pagina(self):
        borrar = reverse("admin:cuentas_usuario_delete", args=[self.ana.pk])
        self.assertEqual(self.client.get(borrar).status_code, 403)
        self.assertEqual(self.client.post(borrar, {"post": "yes"}).status_code, 403)
        self.assertTrue(Usuario.objects.filter(pk=self.ana.pk).exists())

    def test_no_se_puede_eliminar_con_la_accion_masiva(self):
        lista = reverse("admin:cuentas_usuario_changelist")
        respuesta = self.client.post(lista, {"action": "delete_selected", "_selected_action": [self.ana.pk], "post": "yes"},
                                     follow=True)
        self.assertContains(respuesta, "única cuenta admin activa")
        self.assertTrue(Usuario.objects.filter(pk=self.ana.pk).exists())

    def test_con_otro_admin_si_se_puede_eliminar(self):
        crear_usuario("beto@correo.com", rol="admin")
        lista = reverse("admin:cuentas_usuario_changelist")
        self.client.post(lista, {"action": "delete_selected", "_selected_action": [self.ana.pk], "post": "yes"})
        self.assertFalse(Usuario.objects.filter(pk=self.ana.pk).exists())

    def test_se_puede_eliminar_a_otros(self):
        maria = crear_usuario("maria@correo.com")
        self.assertEqual(self.client.get(reverse("admin:cuentas_usuario_delete", args=[maria.pk])).status_code, 200)


class SinAdminTests(TestCase):
    def test_sin_admins_el_enlace_vuelve_y_la_pagina_exige_codigo_nuevo(self):
        # Se crea el primer admin con un código
        with self.assertLogs(LOGGER, "INFO"):
            codigo = servicio.generar_codigo()
            servicio.crear_primer_admin(codigo, "nueva", {"email": "rosa@correo.com", "password1": CLAVE,
                                                          "nombres": "Rosa", "apellidos": "Mera"})
        self.assertEqual(self.client.get(PAGINA).status_code, 404)

        # Alguien la desactiva directo en la base (update() no dispara señales)
        Usuario.objects.update(is_active=False)
        servicio.olvidar_cache()  # equivale a que venza la caché (60 s)
        self.assertContains(self.client.get(ENTRAR), "¿Instalación nueva?")

        # La página vuelve, genera un código NUEVO y el usado no sirve
        with self.assertLogs(LOGGER, "WARNING") as registro:
            self.assertEqual(self.client.get(PAGINA).status_code, 200)
        self.assertIn("CÓDIGO DE CONFIGURACIÓN INICIAL", registro.output[0])
        self.assertNotIn(servicio.formatear(codigo), registro.output[0])
        configuracion = ConfiguracionInicial.obtener()
        self.assertTrue(configuracion.codigo_vigente)
        self.assertFalse(servicio.codigo_correcto(configuracion, codigo))
