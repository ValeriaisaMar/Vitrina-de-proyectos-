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

from cuentas import correo_envio as correo_envio_servicio
from cuentas import limite
from cuentas.cifrado import descifrar, hay_clave
from cuentas.correos import enviar_activacion
from cuentas.decoradores import rol_requerido
from cuentas.forms import (
    FormularioCorreoEnvio,
    FormularioEntrar,
    FormularioFiltroUsuarios,
    FormularioGestionUsuario,
    FormularioPerfil,
    FormularioRegistro,
    FormularioReenvio,
)
from cuentas.models import ConfiguracionCorreo, Rol
from cuentas.perfiles import crear_perfil
from cuentas.roles import activar_rol
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
    return render(request, "cuentas/perfil.html", {
        "form": form,
        "mis_roles": request.user.roles_asignados.order_by("asignado_en"),
    })


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
        Usuario.objects.annotate(total_proyectos=Count("autorias", distinct=True))
        .prefetch_related("roles_asignados")  # las etiquetas de rol sin una consulta por fila
        .order_by("-fecha_registro")
    ).distinct()
    pagina = Paginator(lista, USUARIOS_POR_PAGINA).get_page(request.GET.get("pagina"))
    return render(request, "cuentas/usuarios.html", {"form": form, "pagina": pagina})


@rol_requerido(Rol.ADMIN)
def usuario_editar(request, pk):
    """El admin da o quita roles y activa o desactiva una cuenta. Cada cambio queda registrado."""
    usuario = get_object_or_404(Usuario, pk=pk)
    form = FormularioGestionUsuario(request.POST or None, instance=usuario, editor=request.user)
    if request.method == "POST" and form.is_valid():
        if form.has_changed():
            resumen = form.guardar()
            if resumen:
                # LogEntry es el registro de acciones que ya trae Django: se ve en /admin/
                LogEntry.objects.log_actions(
                    user_id=request.user.pk, queryset=[usuario], action_flag=CHANGE,
                    change_message=resumen, single_object=True,
                )
            messages.success(request, _("Guardamos los cambios de %(nombre)s.") % {"nombre": usuario.nombre_completo})
            if form.es_uno_mismo and not usuario.tiene_rol(Rol.ADMIN):
                # Se quitó el rol admin: la gestión de usuarios ya no es para su rol
                return redirect("vitrina:panel")
        return redirect("cuentas:usuarios")

    return render(request, "cuentas/usuario_editar.html", {
        "form": form,
        "usuario_editado": usuario,
        "es_uno_mismo": usuario.pk == request.user.pk,
        # Si deja de ser profesor, sus proyectos en revisión hay que reasignarlos (spec 009)
        "en_revision": usuario.proyectos_revisados.filter(estado="en_revision").count(),
        "cambios_de_rol": usuario.cambios_de_rol.select_related("hecho_por")[:8],
        "acciones": LogEntry.objects.filter(
            content_type__app_label="cuentas", content_type__model="usuario", object_id=str(usuario.pk)
        ).select_related("user")[:5],
    })


# --------------------------------------------------------------------------- Cambiar de rol (spec 008)


@login_required
@require_POST
def cambiar_rol(request):
    """Cambia el rol con el que actúa la persona y la lleva al panel de ese rol.

    Solo por POST con CSRF. Si pide un rol que no tiene, no cambia nada.
    """
    rol = request.POST.get("rol", "")
    if activar_rol(request, rol):
        messages.success(request, _("Ahora entras como %(rol)s.") % {"rol": Rol(rol).label})
    else:
        messages.error(request, _("No tienes ese rol."))
    return redirect("vitrina:panel")



# --------------------------------------------------------------------------- Correo de envío (spec 008)


@rol_requerido(Rol.ADMIN)
def correo_envio(request):
    """El admin configura desde qué cuenta salen los correos y la prueba sin guardarla.

    - "Guardar": guarda los datos (la contraseña, cifrada; vacía = se conserva la anterior).
    - "Probar configuración": con los datos del formulario, sin guardarlos, envía un correo de
      prueba al correo del admin. Tiene límite de intentos (cuentas/limite.py).
    """
    configuracion = ConfiguracionCorreo.actual()
    inicial = {}
    proveedor = request.GET.get("proveedor")
    if request.method == "GET" and proveedor == "personalizado":
        inicial = FormularioCorreoEnvio(configuracion=configuracion).initial | {"servidor": ""}
    elif request.method == "GET" and proveedor in correo_envio_servicio.PROVEEDORES:
        # Configuración rápida sin JavaScript: ?proveedor=gmail llena servidor, puerto y seguridad
        servidor, puerto, seguridad = correo_envio_servicio.PROVEEDORES[proveedor]
        inicial = FormularioCorreoEnvio(configuracion=configuracion).initial | {"servidor": servidor, "puerto": puerto, "seguridad": seguridad}
    form = FormularioCorreoEnvio(request.POST or None, configuracion=configuracion, **({"initial": inicial} if inicial else {}))
    accion = request.POST.get("accion")
    sin_clave_cifrado = not hay_clave()

    if request.method == "POST" and form.is_valid():
        datos = dict(form.cleaned_data)
        if accion == "probar":
            clave_limite, ip = f"prueba-correo:{request.user.pk}", limite.ip_de(request)
            if limite.esta_bloqueado(clave_limite, ip):
                messages.error(request, _("Hiciste varias pruebas seguidas. Espera unos minutos antes de intentar de nuevo."))
            else:
                limite.registrar_fallo(clave_limite, ip)  # cuenta cada prueba, salga bien o mal
                if not datos["clave"]:
                    datos["clave"] = _clave_guardada(configuracion)
                ok, mensaje = correo_envio_servicio.probar(datos, request.user.email)
                correo_envio_servicio.registrar_prueba(ok, mensaje)
                (messages.success if ok else messages.error)(request, mensaje)
            # Se vuelve a mostrar el formulario con lo escrito (sin la contraseña) para corregir o guardar
            return render(request, "cuentas/correo_envio.html", _contexto_correo(form, configuracion, sin_clave_cifrado, proveedor))

        if datos["clave"] and sin_clave_cifrado:
            messages.error(request, _("No se puede guardar la contraseña: falta la variable CLAVE_CIFRADO en el archivo .env del servidor."))
        else:
            correo_envio_servicio.guardar(datos, request.user, configuracion)
            messages.success(request, _("Guardamos la configuración de correo. Los próximos correos saldrán desde esta cuenta."))
            return redirect("cuentas:correo_envio")

    return render(request, "cuentas/correo_envio.html", _contexto_correo(form, configuracion, sin_clave_cifrado, proveedor))


def _clave_guardada(configuracion):
    """La contraseña guardada, descifrada, para probar sin volver a escribirla. "" si no hay."""
    if not configuracion or not configuracion.tiene_clave:
        return ""
    try:
        return descifrar(configuracion.clave_cifrada)
    except Exception:  # sin CLAVE_CIFRADO o clave cambiada: la prueba fallará con un mensaje claro
        return ""


def _contexto_correo(form, configuracion, sin_clave_cifrado, pedido=None):
    return {
        "form": form,
        "configuracion": configuracion,
        "sin_clave_cifrado": sin_clave_cifrado,
        "proveedores": correo_envio_servicio.PROVEEDORES,
        "remitente_env": settings.EMAIL_REMITENTE,
        "proveedor_activo": correo_envio_servicio.proveedor_de(form, pedido),
    }


# --------------------------------------------------------------------------- Bienvenida al perfil (spec 009)


@login_required
@require_POST
def bienvenida(request):
    """Invitación "Completa tu perfil" del primer inicio de sesión.

    "Completar ahora" lleva a editar el perfil; "Más tarde" la cierra. En los dos casos no vuelve a
    salir: queda un enlace discreto en el panel.
    """
    perfil = crear_perfil(request.user)
    perfil.bienvenida_vista = True
    perfil.save(update_fields=["bienvenida_vista"])
    if request.POST.get("accion") == "ahora" and request.user.tiene_perfil_publico:
        return redirect(perfil.get_absolute_url() + "?editar=1")
    return redirect("vitrina:panel")


# --------------------------------------------------------------------------- Disponibilidad del profesor (spec 009)


@rol_requerido(Rol.PROFESOR)
@require_POST
def disponibilidad(request):
    """Marca o desmarca "Estoy recibiendo proyectos". No afecta a los proyectos que ya tiene asignados."""
    perfil = crear_perfil(request.user)
    perfil.recibiendo_proyectos = request.POST.get("recibiendo") == "1"
    perfil.save(update_fields=["recibiendo_proyectos"])
    if perfil.recibiendo_proyectos:
        messages.success(request, _("Ahora los estudiantes pueden elegirte como revisor."))
    else:
        messages.info(request, _("Ya no apareces como disponible para revisar. Tus proyectos asignados no cambian."))
    return redirect(_destino_seguro(request, request.POST.get("next", "")))


# --------------------------------------------------------------------------- Mi cuenta (spec 009)


@login_required
def mi_cuenta(request):
    """Las opciones del menú del avatar en una página (para navegadores sin JavaScript)."""
    return render(request, "cuentas/mi_cuenta.html")
