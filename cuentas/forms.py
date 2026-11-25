"""Formularios de la app cuentas.

Los de Django vienen pensados para un usuario con "username"; aquí se adaptan al correo y se
agregan los propios del registro, el inicio de sesión, el reenvío de activación y el perfil.
"""

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    AdminUserCreationForm,
    AuthenticationForm,
    BaseUserCreationForm,
    UserChangeForm,
)
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from cuentas.managers import UsuarioManager
from cuentas.models import Rol, Usuario

# --------------------------------------------------------------------------- Panel de Django


class UsuarioCreacionForm(AdminUserCreationForm):
    """Crear un usuario desde el admin."""

    class Meta:
        model = Usuario
        fields = ("email", "nombres", "apellidos", "rol")


class UsuarioCambioForm(UserChangeForm):
    """Editar un usuario desde el admin."""

    class Meta:
        model = Usuario
        fields = ("email", "nombres", "apellidos", "rol", "is_active", "is_staff")


# --------------------------------------------------------------------------- Registro


class FormularioRegistro(BaseUserCreationForm):
    """Registro público. La cuenta queda inactiva hasta abrir el enlace del correo."""

    class Meta:
        model = Usuario
        fields = ("nombres", "apellidos", "email")
        widgets = {
            "nombres": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "apellidos": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "nombre@correo.com"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombres"].widget.attrs["autofocus"] = True
        self.fields["email"].widget.attrs.pop("autofocus", None)
        self.fields["email"].help_text = _("Te enviaremos un enlace para activar tu cuenta.")

    def clean_email(self):
        """Pasa el correo a minúsculas y rechaza los que ya tienen cuenta (sin importar mayúsculas)."""
        email = UsuarioManager.normalizar_correo(self.cleaned_data.get("email"))
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("Ya existe una cuenta con este correo. Si no la has activado, puedes pedir un enlace nuevo."),
                code="duplicado",
            )
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_active = False  # se activa con el enlace del correo
        if commit:
            usuario.save()
        return usuario


# --------------------------------------------------------------------------- Inicio de sesión


class FormularioEntrar(AuthenticationForm):
    """Inicio de sesión con correo, contraseña y la opción de mantener la sesión."""

    username = forms.EmailField(
        label=_("Correo electrónico"),
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email", "placeholder": "nombre@correo.com"}),
    )
    recordar = forms.BooleanField(label=_("Mantener la sesión iniciada"), required=False)

    error_messages = {
        "invalid_login": _("El correo o la contraseña no son correctos."),
        "inactive": _("Tu cuenta aún no está activa. Abre el enlace que te enviamos al correo."),
        "desactivada": _("Tu cuenta está desactivada. Si crees que es un error, escribe a la administración de la carrera."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = _("Contraseña")
        self.cuenta_inactiva = False

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                # authenticate() no devuelve cuentas inactivas. Si la contraseña es correcta,
                # se avisa que falta activar; si no, el mensaje es el genérico.
                inactiva = self._cuenta_inactiva(email, password)
                if inactiva is not None:
                    self.cuenta_inactiva = True
                    if inactiva.last_login is None:  # nunca abrió el enlace de activación
                        raise ValidationError(self.error_messages["inactive"], code="inactive")
                    raise ValidationError(self.error_messages["desactivada"], code="desactivada")
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data

    @staticmethod
    def _cuenta_inactiva(email, password):
        """La cuenta inactiva con ese correo si la contraseña es correcta; si no, None."""
        usuario = Usuario.objects.filter(email__iexact=email, is_active=False).first()
        return usuario if usuario and usuario.check_password(password) else None

    def get_invalid_login_error(self):
        return ValidationError(self.error_messages["invalid_login"], code="invalid_login")


# --------------------------------------------------------------------------- Otros


class FormularioReenvio(forms.Form):
    """Pide el correo para reenviar el enlace de activación."""

    email = forms.EmailField(
        label=_("Correo electrónico"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "nombre@correo.com"}),
    )


class FormularioPerfil(forms.ModelForm):
    """Datos que la persona puede cambiar de su perfil. El correo y el rol no se editan aquí."""

    class Meta:
        model = Usuario
        fields = ("nombres", "apellidos")


# --------------------------------------------------------------------------- Gestión de usuarios (006)


class FormularioFiltroUsuarios(forms.Form):
    """Búsqueda y filtros de la lista de usuarios del admin (por GET)."""

    ESTADOS = [("", _("Todas")), ("activas", _("Activas")), ("sin_activar", _("Sin activar")), ("desactivadas", _("Desactivadas"))]

    q = forms.CharField(label=_("Buscar"), required=False, max_length=100)
    rol = forms.ChoiceField(label=_("Rol"), required=False, choices=[("", _("Todos"))] + list(Rol.choices))
    estado = forms.ChoiceField(label=_("Estado"), required=False, choices=ESTADOS)

    def filtrar(self, usuarios):
        if not self.is_valid():
            return usuarios
        datos = self.cleaned_data
        if datos["q"]:
            q = datos["q"]
            usuarios = usuarios.filter(Q(email__icontains=q) | Q(nombres__icontains=q) | Q(apellidos__icontains=q))
        if datos["rol"]:
            usuarios = usuarios.filter(rol=datos["rol"])
        if datos["estado"] == "activas":
            usuarios = usuarios.filter(is_active=True)
        elif datos["estado"] == "sin_activar":  # nunca abrió el enlace de activación
            usuarios = usuarios.filter(is_active=False, last_login__isnull=True)
        elif datos["estado"] == "desactivadas":  # entró alguna vez y un admin la desactivó
            usuarios = usuarios.filter(is_active=False, last_login__isnull=False)
        return usuarios


class FormularioGestionUsuario(forms.ModelForm):
    """El admin cambia el rol de una cuenta y la activa o desactiva (constitución, principio V).

    Reglas: nadie cambia su propio rol ni se desactiva (así la plataforma nunca se queda sin
    admin por un clic), y las cuentas técnicas (superusuarios de Django) se gestionan en /admin/.
    """

    class Meta:
        model = Usuario
        fields = ("rol", "is_active")
        widgets = {"rol": forms.RadioSelect}
        labels = {"is_active": _("Cuenta activa")}
        help_texts = {"is_active": _("Si la desactivas, no podrá iniciar sesión. Sus proyectos y su historial se conservan.")}

    def __init__(self, *args, editor, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor

    def clean(self):
        datos = super().clean()
        if self.has_changed():
            if self.instance.pk == self.editor.pk:
                raise forms.ValidationError(_("No puedes cambiar tu propio rol ni desactivar tu cuenta. Pídeselo a otro admin."))
            if self.instance.is_superuser:
                raise forms.ValidationError(_("Esta es una cuenta técnica de Django: su rol y estado se cambian en /admin/."))
        return datos

    def resumen_cambios(self):
        """Texto para el registro de acciones, por ejemplo: «Rol: Estudiante → Profesor»."""
        partes = []
        if "rol" in self.changed_data:
            antes = Rol(self.initial["rol"]).label
            partes.append(f"Rol: {antes} → {self.instance.get_rol_display()}")
        if "is_active" in self.changed_data:
            partes.append(f"Cuenta activa: {'sí' if self.initial['is_active'] else 'no'} → {'sí' if self.instance.is_active else 'no'}")
        return ". ".join(partes)
