"""Pruebas de la gestión de usuarios y roles por el admin (módulo 006)."""

from django.contrib.admin.models import LogEntry
from django.test import TestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import CLAVE, crear_usuario

LISTA = reverse("cuentas:usuarios")


def editar(usuario):
    return reverse("cuentas:usuario_editar", args=[usuario.pk])


class AccesoTests(TestCase):
    def test_solo_admins(self):
        objetivo = crear_usuario("ana@correo.com")
        self.assertEqual(self.client.get(LISTA).status_code, 302)
        for rol in (Rol.ESTUDIANTE, Rol.PROFESOR):
            self.client.force_login(crear_usuario(f"{rol}@correo.com", rol=rol))
            self.assertEqual(self.client.get(LISTA).status_code, 403)
            self.assertEqual(self.client.post(editar(objetivo), {"rol": Rol.ADMIN, "is_active": "on"}).status_code, 403)
        objetivo.refresh_from_db()
        self.assertEqual(objetivo.rol, Rol.ESTUDIANTE)


class ListaTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.client.force_login(self.admin)
        crear_usuario("ana@correo.com", nombres="Ana", apellidos="Zambrano")
        crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        crear_usuario("pendiente@correo.com", activo=False)

    def correos(self, **filtros):
        return {u.email for u in self.client.get(LISTA, filtros).context["pagina"].object_list}

    def test_busqueda_y_filtros(self):
        self.assertEqual(self.correos(q="zambrano"), {"ana@correo.com"})
        self.assertEqual(self.correos(rol="profesor"), {"profe@correo.com"})
        self.assertEqual(self.correos(estado="sin_activar"), {"pendiente@correo.com"})
        self.assertEqual(len(self.correos()), 4)

    def test_valores_raros_no_rompen(self):
        self.assertEqual(self.client.get(LISTA, {"rol": "rey", "pagina": "x"}).status_code, 200)

    def test_paginacion(self):
        for i in range(20):
            crear_usuario(f"e{i}@correo.com")
        self.assertEqual(len(self.client.get(LISTA).context["pagina"].object_list), 20)
        self.assertEqual(len(self.client.get(LISTA, {"pagina": 2}).context["pagina"].object_list), 4)


class EditarTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN, nombres="Root", apellidos="Admin")
        self.ana = crear_usuario("ana@correo.com")
        self.client.force_login(self.admin)

    def test_nombrar_profesor_queda_registrado(self):
        respuesta = self.client.post(editar(self.ana), {"rol": Rol.PROFESOR, "is_active": "on"})
        self.assertRedirects(respuesta, LISTA)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.rol, Rol.PROFESOR)
        self.assertFalse(self.ana.is_staff)  # el rol no da acceso a /admin/
        accion = LogEntry.objects.get()
        self.assertEqual((accion.user, accion.object_id), (self.admin, str(self.ana.pk)))
        self.assertIn("Estudiante → Profesor", accion.change_message)
        self.assertContains(self.client.get(editar(self.ana)), "Estudiante → Profesor")

    def test_sin_cambios_no_registra_nada(self):
        self.client.post(editar(self.ana), {"rol": Rol.ESTUDIANTE, "is_active": "on"})
        self.assertFalse(LogEntry.objects.exists())

    def test_desactivar_impide_entrar_y_cierra_la_sesion(self):
        otra_sesion = self.client_class()
        otra_sesion.force_login(self.ana)
        self.client.post(editar(self.ana), {"rol": Rol.ESTUDIANTE})  # casilla sin marcar = desactivar
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_active)
        self.assertFalse(otra_sesion.login(username=self.ana.email, password=CLAVE))
        self.assertEqual(otra_sesion.get(reverse("vitrina:panel")).status_code, 302)

    def test_activar_a_mano_una_cuenta_pendiente(self):
        pendiente = crear_usuario("pendiente@correo.com", activo=False)
        self.client.post(editar(pendiente), {"rol": Rol.ESTUDIANTE, "is_active": "on"})
        pendiente.refresh_from_db()
        self.assertTrue(pendiente.is_active)

    def test_no_puede_cambiarse_a_si_mismo(self):
        respuesta = self.client.post(editar(self.admin), {"rol": Rol.ESTUDIANTE, "is_active": "on"})
        self.assertEqual(respuesta.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.rol, Rol.ADMIN)
        self.assertContains(respuesta, "otro admin")

    def test_las_cuentas_tecnicas_no_se_tocan(self):
        root = crear_usuario("root@correo.com", rol=Rol.ADMIN, is_staff=True, is_superuser=True)
        self.client.post(editar(root), {"rol": Rol.ESTUDIANTE, "is_active": "on"})
        root.refresh_from_db()
        self.assertEqual(root.rol, Rol.ADMIN)

    def test_avisa_si_el_profesor_tiene_revisiones(self):
        from proyectos.models import Estado
        from proyectos.servicios import cambiar_estado
        from proyectos.tests.utilidades import crear_proyecto

        profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        proyecto = crear_proyecto(self.ana)
        cambiar_estado(proyecto, Estado.ENVIADO, self.ana)
        cambiar_estado(proyecto, Estado.EN_REVISION, profe)
        self.assertContains(self.client.get(editar(profe)), "un admin tendrá que decidirlos")

    def test_usuario_inexistente(self):
        self.assertEqual(self.client.get(reverse("cuentas:usuario_editar", args=[99999])).status_code, 404)
