"""Pruebas del usuario en el panel de administración de Django."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from cuentas.models import Rol

Usuario = get_user_model()


class UsuarioAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_superuser(
            email="admin@uteq.edu.ec", password="clave-segura-123", nombres="Ada", apellidos="Admin"
        )
        cls.estudiante = Usuario.objects.create_user(
            email="maria@correo.com", password="clave-segura-123", nombres="María", apellidos="Vera"
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_lista_de_usuarios(self):
        respuesta = self.client.get(reverse("admin:cuentas_usuario_changelist"))
        self.assertContains(respuesta, "maria@correo.com")

    def test_buscar_por_nombre(self):
        respuesta = self.client.get(reverse("admin:cuentas_usuario_changelist"), {"q": "María"})
        self.assertContains(respuesta, "maria@correo.com")
        self.assertNotContains(respuesta, "admin@uteq.edu.ec</a>")

    def test_buscar_por_correo(self):
        respuesta = self.client.get(reverse("admin:cuentas_usuario_changelist"), {"q": "maria@"})
        self.assertContains(respuesta, "maria@correo.com")

    def test_paginas_de_crear_y_editar_abren(self):
        self.assertEqual(self.client.get(reverse("admin:cuentas_usuario_add")).status_code, 200)
        editar = reverse("admin:cuentas_usuario_change", args=[self.estudiante.pk])
        self.assertEqual(self.client.get(editar).status_code, 200)

    def test_el_admin_cambia_el_rol(self):
        editar = reverse("admin:cuentas_usuario_change", args=[self.estudiante.pk])
        respuesta = self.client.post(editar, {
            "email": "maria@correo.com", "nombres": "María", "apellidos": "Vera",
            "rol": Rol.PROFESOR, "is_active": "on",
            "fecha_registro_0": "2026-11-23", "fecha_registro_1": "10:00:00",
        })
        self.assertEqual(respuesta.status_code, 302, getattr(respuesta, "context", None) and respuesta.context["adminform"].form.errors)
        self.estudiante.refresh_from_db()
        self.assertEqual(self.estudiante.rol, Rol.PROFESOR)

    def test_el_admin_crea_un_usuario(self):
        respuesta = self.client.post(reverse("admin:cuentas_usuario_add"), {
            "email": "Nuevo@Correo.com", "nombres": "Nuevo", "apellidos": "Usuario", "rol": Rol.ESTUDIANTE,
            "usable_password": "true", "password1": "una-clave-larga-123", "password2": "una-clave-larga-123",
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Usuario.objects.filter(email="nuevo@correo.com").exists())
