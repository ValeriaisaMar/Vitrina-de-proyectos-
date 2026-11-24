"""Pruebas del usuario propio: correo como identificador, rol y autenticación."""

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from cuentas.models import Rol

Usuario = get_user_model()


class UsuarioModeloTests(TestCase):
    def crear(self, email="Ana@Correo.COM", **extra):
        datos = {"nombres": "Ana", "apellidos": "Pérez", **extra}
        return Usuario.objects.create_user(email=email, password="clave-segura-123", **datos)

    def test_el_modelo_de_usuario_es_el_propio(self):
        self.assertEqual(Usuario._meta.label, "cuentas.Usuario")

    def test_el_correo_se_guarda_en_minusculas(self):
        self.assertEqual(self.crear().email, "ana@correo.com")

    def test_el_correo_es_unico_sin_importar_mayusculas(self):
        self.crear()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear(email="ANA@correo.com")

    def test_valores_por_defecto(self):
        usuario = self.crear()
        self.assertEqual(usuario.rol, Rol.ESTUDIANTE)
        self.assertTrue(usuario.es_estudiante)
        self.assertFalse(usuario.is_active)  # se activa con el correo (módulo 002)
        self.assertFalse(usuario.is_staff)

    def test_la_contrasena_se_guarda_cifrada(self):
        usuario = self.crear()
        self.assertNotEqual(usuario.password, "clave-segura-123")
        self.assertTrue(usuario.check_password("clave-segura-123"))

    def test_nombre_completo_y_texto(self):
        usuario = self.crear()
        self.assertEqual(usuario.nombre_completo, "Ana Pérez")
        self.assertEqual(str(usuario), "Ana Pérez")

    def test_el_superusuario_es_admin_y_activo(self):
        admin = Usuario.objects.create_superuser(
            email="Admin@UTEQ.edu.ec", password="clave-segura-123", nombres="Ad", apellidos="Min"
        )
        self.assertEqual(admin.rol, Rol.ADMIN)
        self.assertTrue(admin.es_admin)
        self.assertTrue(admin.is_active and admin.is_staff and admin.is_superuser)

    def test_crear_sin_correo_falla(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(email="", password="x", nombres="A", apellidos="B")

    def test_roles_disponibles(self):
        self.assertEqual(set(Rol.values), {"estudiante", "profesor", "admin"})


class AutenticacionTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email="luis@correo.com", password="clave-segura-123",
            nombres="Luis", apellidos="Mora", is_active=True,
        )

    def test_inicia_sesion_con_el_correo_en_cualquier_mayuscula(self):
        self.assertEqual(authenticate(email="LUIS@Correo.com", password="clave-segura-123"), self.usuario)

    def test_contrasena_incorrecta_no_entra(self):
        self.assertIsNone(authenticate(email="luis@correo.com", password="otra"))

    def test_cuenta_inactiva_no_entra(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.assertIsNone(authenticate(email="luis@correo.com", password="clave-segura-123"))

    def test_formulario_de_login_funciona_con_el_correo(self):
        respuesta = self.client.post(
            "/cuentas/login/", {"username": "Luis@correo.com", "password": "clave-segura-123"}
        )
        self.assertRedirects(respuesta, "/")
