"""Historia 4: ver y editar el perfil y cambiar la contraseña."""

from django.test import TestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import CLAVE, crear_usuario

NUEVA = "otra-clave-muy-segura-456"


class PerfilTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario()
        self.client.force_login(self.usuario)

    def test_sin_sesion_lleva_a_iniciar_sesion(self):
        self.client.logout()
        respuesta = self.client.get(reverse("cuentas:perfil"))
        self.assertRedirects(respuesta, f"{reverse('cuentas:entrar')}?next={reverse('cuentas:perfil')}")

    def test_muestra_los_datos_y_el_rol(self):
        respuesta = self.client.get(reverse("cuentas:perfil"))
        self.assertContains(respuesta, "ana@correo.com")
        self.assertContains(respuesta, "Estudiante")

    def test_edita_nombres_y_apellidos(self):
        respuesta = self.client.post(reverse("cuentas:perfil"), {"nombres": "Ana María", "apellidos": "Pérez Ruiz"}, follow=True)
        self.assertContains(respuesta, "Guardamos los cambios de tu perfil.")
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre_completo, "Ana María Pérez Ruiz")

    def test_no_permite_cambiar_correo_ni_rol(self):
        self.client.post(reverse("cuentas:perfil"), {
            "nombres": "Ana", "apellidos": "Pérez", "email": "otro@correo.com", "rol": Rol.ADMIN,
        })
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "ana@correo.com")
        self.usuario.olvidar_roles()
        self.assertEqual(self.usuario.roles, [Rol.ESTUDIANTE])

    def test_cambia_la_contrasena_y_sigue_con_sesion(self):
        respuesta = self.client.post(reverse("cuentas:cambiar_contrasena"), {
            "old_password": CLAVE, "new_password1": NUEVA, "new_password2": NUEVA,
        }, follow=True)
        self.assertContains(respuesta, "Tu contraseña cambió.")
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(NUEVA))
        self.assertIn("_auth_user_id", self.client.session)

    def test_la_contrasena_actual_es_obligatoria(self):
        self.client.post(reverse("cuentas:cambiar_contrasena"), {
            "old_password": "equivocada", "new_password1": NUEVA, "new_password2": NUEVA,
        })
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(CLAVE))


class MisRolesSinFechaTests(TestCase):
    """La fecha ya sale en "Miembro desde"; en "Mis roles" solo van el rol y si está activo."""

    def test_mis_roles_no_repite_la_fecha(self):
        from cuentas.tests.utilidades import crear_usuario as nuevo

        self.client.force_login(nuevo(email="roles@correo.com"))
        html = self.client.get(reverse("cuentas:perfil")).content.decode()
        roles = html[html.index('id="titulo-mis-roles"'):]
        roles = roles[:roles.index("</section>")]
        self.assertNotIn("desde el", roles)
        self.assertIn("activo", roles)
