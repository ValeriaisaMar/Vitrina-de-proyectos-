"""Rutas de la app cuentas. Se usan como {% url 'cuentas:entrar' %}."""

from django.contrib.auth import views as auth
from django.urls import path, reverse_lazy

from cuentas import views

app_name = "cuentas"

urlpatterns = [
    # Registro y activación
    path("registro/", views.registro, name="registro"),
    path("registro/revisa-tu-correo/", views.revisa_correo, name="revisa_correo"),
    path("activar/<uidb64>/<token>/", views.activar, name="activar"),
    path("activacion/reenviar/", views.reenviar_activacion, name="reenviar"),
    # Entrar y salir
    path("entrar/", views.entrar, name="entrar"),
    path("salir/", views.salir, name="salir"),
    path("cambiar-rol/", views.cambiar_rol, name="cambiar_rol"),
    # Perfil
    path("perfil/", views.perfil, name="perfil"),
    path("perfil/contrasena/", views.CambiarContrasena.as_view(), name="cambiar_contrasena"),
    # Recuperar contraseña: vistas de Django con nuestras plantillas y correos
    path("contrasena/recuperar/", auth.PasswordResetView.as_view(
        template_name="cuentas/recuperar.html",
        email_template_name="cuentas/correos/recuperacion.txt",
        html_email_template_name="cuentas/correos/recuperacion.html",
        subject_template_name="cuentas/correos/recuperacion_asunto.txt",
        success_url=reverse_lazy("cuentas:recuperar_enviado"),
    ), name="recuperar"),
    path("contrasena/recuperar/enviado/", auth.PasswordResetDoneView.as_view(
        template_name="cuentas/recuperar_enviado.html",
    ), name="recuperar_enviado"),
    path("contrasena/nueva/<uidb64>/<token>/", auth.PasswordResetConfirmView.as_view(
        template_name="cuentas/recuperar_confirmar.html",
        success_url=reverse_lazy("cuentas:recuperar_listo"),
    ), name="recuperar_confirmar"),
    path("contrasena/nueva/lista/", auth.PasswordResetCompleteView.as_view(
        template_name="cuentas/recuperar_listo.html",
    ), name="recuperar_listo"),
    # Gestión de usuarios (solo admins, módulo 006)
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuarios/<int:pk>/", views.usuario_editar, name="usuario_editar"),
    # Correo de envío (solo admins, spec 008)
    path("correo-de-envio/", views.correo_envio, name="correo_envio"),
]
