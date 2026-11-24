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
from django.utils.translation import gettext_lazy as _

from cuentas.managers import UsuarioManager
from cuentas.models import Usuario

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
                if self._es_cuenta_inactiva(email, password):
                    self.cuenta_inactiva = True
                    raise ValidationError(self.error_messages["inactive"], code="inactive")
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data

    @staticmethod
    def _es_cuenta_inactiva(email, password):
        usuario = Usuario.objects.filter(email__iexact=email, is_active=False).first()
        return bool(usuario and usuario.check_password(password))

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
