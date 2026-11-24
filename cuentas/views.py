"""Vistas de la app cuentas: registro, activación, inicio y cierre de sesión y perfil.

La recuperación y el cambio de contraseña usan las vistas de Django (ver urls.py), porque ya
resuelven los tokens y las validaciones de forma segura; aquí solo se adaptan los mensajes.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from cuentas import limite
from cuentas.correos import enviar_activacion
from cuentas.forms import FormularioEntrar, FormularioPerfil, FormularioRegistro, FormularioReenvio
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

    if usuario is not None and not usuario.is_active and token_activacion.check_token(usuario, token):
        usuario.is_active = True
        usuario.save(update_fields=["is_active"])
        login(request, usuario, backend=BACKEND)
        request.session.pop("correo_pendiente", None)
        messages.success(request, _("Tu cuenta está activa. ¡Bienvenido a la Vitrina!"))
        return redirect("vitrina:inicio")

    return render(request, "cuentas/activacion_invalida.html", {"form": FormularioReenvio()}, status=400)


def reenviar_activacion(request):
    """Reenvía el enlace a una cuenta inactiva. Responde igual exista o no el correo."""
    form = FormularioReenvio(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        usuario = Usuario.objects.filter(email__iexact=email, is_active=False).first()
        if usuario is not None:
            enviar_activacion(request, usuario)
        request.session["correo_pendiente"] = email.lower()
        request.session["modo_reenvio"] = True
        return redirect("cuentas:revisa_correo")
    return render(request, "cuentas/reenviar.html", {"form": form})


# --------------------------------------------------------------------------- Entrar y salir


def _destino_seguro(request, destino):
    """Devuelve el destino solo si es del mismo sitio; si no, el inicio (evita redirecciones abiertas)."""
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()},
                                                   require_https=request.is_secure()):
        return destino
    return reverse("vitrina:inicio")


def entrar(request):
    """Inicio de sesión con correo y contraseña, con límite de intentos fallidos."""
    if request.user.is_authenticated:
        return redirect("vitrina:inicio")

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
