"""Vistas de la app cuentas: registro, activación, inicio y cierre de sesión y perfil.

La recuperación y el cambio de contraseña usan las vistas de Django (ver urls.py), porque ya
resuelven los tokens y las validaciones de forma segura; aquí solo se adaptan los mensajes.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.views import PasswordChangeView
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from cuentas import limite
from cuentas.decoradores import rol_requerido
from cuentas.correos import enviar_activacion
from cuentas.forms import (
    FormularioEntrar,
    FormularioFiltroUsuarios,
    FormularioGestionUsuario,
    FormularioPerfil,
    FormularioRegistro,
    FormularioReenvio,
)
from cuentas.models import Rol
from cuentas.tokens import token_activacion

Usuario = get_user_model()
BACKEND = "django.contrib.auth.backends.ModelBackend"


# --------------------------------------------------------------------------- Registro


def registro(request):
    """Crea la cuenta inactiva y envía el enlace de activación."""
    if request.user.is_authenticated:
        return redirect("vitrina:inicio")

    form = FormularioRegistro(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        enviado = enviar_activacion(request, usuario)
        request.session["correo_pendiente"] = usuario.email
        request.session["correo_fallo"] = not enviado
        return redirect("cuentas:revisa_correo")

    return render(request, "cuentas/registro.html", {"form": form})


def revisa_correo(request):
    """Página "Revisa tu correo" después del registro o del reenvío."""
    return render(request, "cuentas/revisa_correo.html", {
        "correo": request.session.get("correo_pendiente"),
        "fallo": request.session.pop("correo_fallo", False),
        "reenvio": request.session.pop("modo_reenvio", False),
    })


def activar(request, uidb64, token):
    """Activa la cuenta si el enlace es válido e inicia la sesión."""
    try:
        usuario = Usuario.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None

    # Solo cuentas que nunca se activaron (activar inicia sesión, así que llenan last_login).
    # Una cuenta que un admin desactivó no se puede reactivar con un enlace.
    if (usuario is not None and not usuario.is_active and usuario.last_login is None
            and token_activacion.check_token(usuario, token)):
        usuario.is_active = True
        usuario.save(update_fields=["is_active"])
        login(request, usuario, backend=BACKEND)
        request.session.pop("correo_pendiente", None)
        messages.success(request, _("Tu cuenta está activa. ¡Bienvenido a la Vitrina!"))
        return redirect(settings.LOGIN_REDIRECT_URL)  # su panel

    return render(request, "cuentas/activacion_invalida.html", {"form": FormularioReenvio()}, status=400)


def reenviar_activacion(request):
    """Reenvía el enlace a una cuenta inactiva. Responde igual exista o no el correo."""
    form = FormularioReenvio(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        # Solo cuentas sin activar: las desactivadas por un admin no reciben enlace
        usuario = Usuario.objects.filter(email__iexact=email, is_active=False, last_login__isnull=True).first()
        if usuario is not None:
            enviar_activacion(request, usuario)
        request.session["correo_pendiente"] = email.lower()
        request.session["modo_reenvio"] = True
        return redirect("cuentas:revisa_correo")
    return render(request, "cuentas/reenviar.html", {"form": form})


# --------------------------------------------------------------------------- Entrar y salir


def _destino_seguro(request, destino):
    """Devuelve el destino solo si es del mismo sitio; si no, el panel (evita redirecciones abiertas)."""
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()},
                                                   require_https=request.is_secure()):
        return destino
    return resolve_url(settings.LOGIN_REDIRECT_URL)


def entrar(request):
    """Inicio de sesión con correo y contraseña, con límite de intentos fallidos."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    siguiente = request.POST.get("next") or request.GET.get("next", "")
    bloqueado = False

    if request.method == "POST":
        email = request.POST.get("username", "")
        ip = limite.ip_de(request)
        form = FormularioEntrar(request, data=request.POST)

        if limite.esta_bloqueado(email, ip):
            bloqueado = True
        elif form.is_valid():
            limite.limpiar(email, ip)
            login(request, form.get_user())
            if not form.cleaned_data.get("recordar"):
                request.session.set_expiry(0)  # la sesión termina al cerrar el navegador
            return redirect(_destino_seguro(request, siguiente))
        elif not form.cuenta_inactiva:
            limite.registrar_fallo(email, ip)
    else:
        form = FormularioEntrar(request)

    return render(request, "cuentas/entrar.html", {
        "form": form,
        "next": siguiente,
        "bloqueado": bloqueado,
        "minutos": limite.BLOQUEO_SEGUNDOS // 60,
    })


@require_POST
def salir(request):
    """Cierra la sesión. Solo por POST, para que un enlace externo no pueda cerrarla."""
    logout(request)
    messages.info(request, _("Cerraste sesión."))
    return redirect("vitrina:inicio")


# --------------------------------------------------------------------------- Perfil


@login_required
def perfil(request):
    """Muestra los datos de la persona y le permite corregir nombres y apellidos."""
    form = FormularioPerfil(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Guardamos los cambios de tu perfil."))
        return redirect("cuentas:perfil")
    return render(request, "cuentas/perfil.html", {"form": form})


class CambiarContrasena(PasswordChangeView):
    """Cambio de contraseña con la vista de Django; mantiene la sesión abierta."""

    template_name = "cuentas/contrasena_cambiar.html"
    success_url = reverse_lazy("cuentas:perfil")

    def form_valid(self, form):
        messages.success(self.request, _("Tu contraseña cambió."))
        return super().form_valid(form)


# --------------------------------------------------------------------------- Gestión de usuarios (006)

USUARIOS_POR_PAGINA = 20


@rol_requerido(Rol.ADMIN)
def usuarios(request):
    """Lista de cuentas con búsqueda y filtros, solo para admins."""
    form = FormularioFiltroUsuarios(request.GET or None)
    lista = form.filtrar(
        Usuario.objects.annotate(total_proyectos=Count("autorias")).order_by("-fecha_registro")
    )
    pagina = Paginator(lista, USUARIOS_POR_PAGINA).get_page(request.GET.get("pagina"))
    return render(request, "cuentas/usuarios.html", {"form": form, "pagina": pagina})


@rol_requerido(Rol.ADMIN)
def usuario_editar(request, pk):
    """El admin cambia el rol o el estado de una cuenta. Cada cambio queda en el registro de acciones."""
    usuario = get_object_or_404(Usuario, pk=pk)
    form = FormularioGestionUsuario(request.POST or None, instance=usuario, editor=request.user)
    if request.method == "POST" and form.is_valid():
        if form.has_changed():
            form.save()
            # LogEntry es el registro de acciones que ya trae Django: se ve en /admin/
            LogEntry.objects.log_actions(
                user_id=request.user.pk, queryset=[usuario], action_flag=CHANGE,
                change_message=form.resumen_cambios(), single_object=True,
            )
            messages.success(request, _("Guardamos los cambios de %(nombre)s.") % {"nombre": usuario.nombre_completo})
        return redirect("cuentas:usuarios")

    return render(request, "cuentas/usuario_editar.html", {
        "form": form,
        "usuario_editado": usuario,
        "es_uno_mismo": usuario.pk == request.user.pk,
        # Si un profesor deja de serlo, sus proyectos en revisión los tendrá que decidir un admin
        "en_revision": usuario.proyectos_revisados.filter(estado="en_revision").count(),
        "acciones": LogEntry.objects.filter(
            content_type__app_label="cuentas", content_type__model="usuario", object_id=str(usuario.pk)
        ).select_related("user")[:5],
    })

