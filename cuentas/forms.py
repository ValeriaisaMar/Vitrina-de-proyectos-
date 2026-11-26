"""Formularios de la app cuentas.

Los de Django vienen pensados para un usuario con "username"; aquí se adaptan al correo y se
agregan los propios del registro, el inicio de sesión, el reenvío de activación y el perfil.
"""

import logging

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    AdminUserCreationForm,
    AuthenticationForm,
    BaseUserCreationForm,
    PasswordResetForm,
    UserChangeForm,
)
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from config.correo import CorreoConLogo
from config.texto import FormularioNFC
from cuentas import roles as servicio_roles
from cuentas.managers import UsuarioManager
from cuentas.models import Aptitud, Estudio, ExperienciaLaboral, Perfil, Rol, RolAsignado, Seguridad, Usuario

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- Panel de Django


class UsuarioCreacionForm(AdminUserCreationForm):
    """Crear un usuario desde el admin. Los roles se agregan después, en la misma página."""

    class Meta:
        model = Usuario
        fields = ("email", "nombres", "apellidos")


MENSAJE_ULTIMO_ADMIN = _("No puedes desactivar esta cuenta: es la única cuenta admin activa. Primero nombra a otro admin.")


def desactiva_al_ultimo_admin(form):
    """True si el formulario apaga is_active de la única cuenta admin activa (spec 010, historia 4).

    Si se quedara sin admins, la configuración inicial se volvería a abrir.
    """
    return ("is_active" in form.changed_data and not form.cleaned_data.get("is_active")
            and servicio_roles.es_ultimo_admin(form.instance))


class UsuarioCambioForm(UserChangeForm):
    """Editar un usuario desde el admin."""

    class Meta:
        model = Usuario
        fields = ("email", "nombres", "apellidos", "is_active", "is_staff")

    def clean(self):
        datos = super().clean()
        if desactiva_al_ultimo_admin(self):
            self.add_error("is_active", MENSAJE_ULTIMO_ADMIN)
        return datos


# --------------------------------------------------------------------------- Registro


class FormularioRegistro(FormularioNFC, BaseUserCreationForm):
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
            RolAsignado.objects.create(usuario=usuario, rol=Rol.ESTUDIANTE)  # toda cuenta nace estudiante
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


class FormularioPerfil(FormularioNFC, forms.ModelForm):
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
        if datos["rol"]:  # quien TIENE ese rol, aunque ahora actúe con otro
            usuarios = usuarios.filter(roles_asignados__rol=datos["rol"])
        if datos["estado"] == "activas":
            usuarios = usuarios.filter(is_active=True)
        elif datos["estado"] == "sin_activar":  # nunca abrió el enlace de activación
            usuarios = usuarios.filter(is_active=False, last_login__isnull=True)
        elif datos["estado"] == "desactivadas":  # entró alguna vez y un admin la desactivó
            usuarios = usuarios.filter(is_active=False, last_login__isnull=False)
        return usuarios


class FormularioGestionUsuario(forms.ModelForm):
    """El admin da o quita roles a una cuenta y la activa o desactiva (constitución, principio V).

    Reglas (spec 008):
    - Una casilla por rol; toda cuenta conserva al menos uno.
    - No se le quita el rol admin al último admin activo (lo valida cuentas/roles.py).
    - Quitarse el rol admin a uno mismo pide marcar una casilla de confirmación.
    - Nadie se desactiva a sí mismo, y las cuentas técnicas (superusuarios de Django) se gestionan en /admin/.
    """

    roles = forms.MultipleChoiceField(
        label=_("Roles"), choices=Rol.choices, required=False, widget=forms.CheckboxSelectMultiple,
    )
    confirmar_quitar_admin = forms.BooleanField(
        label=_("Sí, quiero dejar de ser admin. Entiendo que perderé el acceso a la gestión de usuarios."),
        required=False,
    )

    class Meta:
        model = Usuario
        fields = ("is_active",)
        labels = {"is_active": _("Cuenta activa")}
        help_texts = {"is_active": _("Si la desactivas, no podrá iniciar sesión. Sus proyectos y su historial se conservan.")}

    def __init__(self, *args, editor, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor
        self.es_uno_mismo = self.instance.pk == editor.pk
        self.fields["roles"].initial = self.instance.roles
        if self.es_uno_mismo:
            # Un campo deshabilitado ignora lo que llegue en el POST y conserva el valor actual
            self.fields["is_active"].disabled = True
        # La casilla de confirmación solo aparece cuando hace falta (ver clean)
        self.pide_confirmacion = False

    def clean_roles(self):
        return servicio_roles.ordenar(self.cleaned_data.get("roles") or [])

    def clean(self):
        datos = super().clean()
        if not self.has_changed():
            return datos
        if self.instance.is_superuser:
            raise forms.ValidationError(_("Esta es una cuenta técnica de Django: sus roles y su estado se cambian en /admin/."))
        if self.es_uno_mismo and "is_active" in self.changed_data:
            raise forms.ValidationError(_("No puedes desactivar tu propia cuenta. Pídeselo a otro admin."))
        if desactiva_al_ultimo_admin(self):
            raise forms.ValidationError(MENSAJE_ULTIMO_ADMIN)
        if "roles" in datos:
            try:
                servicio_roles.validar_roles(self.instance, datos["roles"])
            except forms.ValidationError as error:
                self.add_error("roles", error)
                return datos
            quita_admin = self.instance.tiene_rol(Rol.ADMIN) and Rol.ADMIN not in datos["roles"]
            if self.es_uno_mismo and quita_admin and not datos.get("confirmar_quitar_admin"):
                self.pide_confirmacion = True
                self.add_error("confirmar_quitar_admin", _("Confirma que quieres quitarte el rol admin."))
        return datos

    def guardar(self):
        """Guarda el estado de la cuenta y los roles. Devuelve el texto para el registro de acciones."""
        partes = []
        if "is_active" in self.changed_data:
            self.save()
            partes.append(f"Cuenta activa: {'sí' if self.initial['is_active'] else 'no'} → {'sí' if self.instance.is_active else 'no'}")
        agregados, quitados = servicio_roles.asignar_roles(self.instance, self.cleaned_data["roles"], self.editor)
        if agregados or quitados:
            partes.append(servicio_roles.resumen(agregados, quitados))
        return ". ".join(partes)


# --------------------------------------------------------------------------- Correo de envío (spec 008)


class FormularioCorreoEnvio(forms.Form):
    """Datos de la cuenta desde la que la plataforma envía sus correos.

    La contraseña nunca se vuelve a mostrar: el campo siempre llega vacío y, si se deja vacío,
    se conserva la que estaba guardada.
    """

    servidor = forms.CharField(label=_("Servidor SMTP"), max_length=120, widget=forms.TextInput(attrs={"placeholder": "smtp.gmail.com", "autocomplete": "off"}))
    puerto = forms.IntegerField(label=_("Puerto"), min_value=1, max_value=65535, initial=587)
    seguridad = forms.ChoiceField(label=_("Seguridad"), choices=Seguridad.choices, initial=Seguridad.STARTTLS)
    usuario = forms.CharField(
        label=_("Usuario o correo de acceso"), max_length=254,
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "vitrinadeproyectosuteq@gmail.com"}),
    )
    clave = forms.CharField(
        label=_("Contraseña de aplicación"), required=False, strip=True,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
    )
    nombre_remitente = forms.CharField(label=_("Nombre del remitente"), max_length=80, initial="Vitrina de Proyectos UTEQ")
    correo_remitente = forms.EmailField(
        label=_("Correo del remitente"), required=False,
        help_text=_("Opcional. Si lo dejas vacío se usa el mismo usuario de acceso."),
    )

    def __init__(self, *args, configuracion=None, **kwargs):
        if configuracion is not None and "initial" not in kwargs:
            kwargs["initial"] = {
                campo: getattr(configuracion, campo)
                for campo in ("servidor", "puerto", "seguridad", "usuario", "nombre_remitente", "correo_remitente")
            }
        super().__init__(*args, **kwargs)
        self.configuracion = configuracion
        self.tiene_clave = bool(configuracion and configuracion.tiene_clave)
        if self.tiene_clave:
            self.fields["clave"].help_text = _("Contraseña guardada. Déjala vacía para conservarla, o escribe una nueva para cambiarla.")
        else:
            self.fields["clave"].help_text = _("Los 16 caracteres que te da Google, sin espacios.")

    def clean_clave(self):
        # Google muestra la contraseña de aplicación en grupos de 4 con espacios: se quitan
        return "".join((self.cleaned_data.get("clave") or "").split())

    def clean(self):
        datos = super().clean()
        if not datos.get("clave") and not self.tiene_clave:
            self.add_error("clave", _("Escribe la contraseña de aplicación."))
        return datos


# --------------------------------------------------------------------------- Perfil público (spec 009, historia 4)

MAX_APTITUDES = 15
FORMATO_MES = "%Y-%m"


class CampoMes(forms.DateField):
    """Mes y año (<input type="month">). Se guarda como el día 1 de ese mes."""

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", [FORMATO_MES, "%Y-%m-%d"])
        kwargs.setdefault("widget", forms.DateInput(attrs={"type": "month"}, format=FORMATO_MES))
        super().__init__(**kwargs)


class FormularioFoto(forms.Form):
    """Foto de perfil: imagen real JPG, PNG o WEBP de hasta 5 MB; se guarda como webp cuadrado."""

    foto = forms.FileField(label=_("Foto de perfil"), widget=forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
                           help_text=_("JPG, PNG o WEBP de hasta 5 MB. Se recorta en cuadrado."))

    def clean_foto(self):
        from config.imagenes import validar_imagen_subida

        foto = self.cleaned_data["foto"]
        validar_imagen_subida(foto)
        return foto


class FormularioDescripcion(FormularioNFC, forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ("descripcion",)
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 4, "maxlength": 600})}
        help_texts = {"descripcion": _("Máximo 600 caracteres. Cuenta quién eres y qué te interesa.")}


class FormularioAptitudes(FormularioNFC, forms.Form):
    """Aptitudes separadas por comas. Se reutilizan las que ya existen sin distinguir mayúsculas."""

    aptitudes = forms.CharField(
        label=_("Aptitudes"), required=False, max_length=800,
        widget=forms.TextInput(attrs={"list": "aptitudes-existentes", "autocomplete": "off", "placeholder": "Django, Flutter, Diseño UX"}),
        help_text=_("Sepáralas con comas. Máximo 15."),
    )

    def clean_aptitudes(self):
        nombres, vistos = [], set()
        for parte in (self.cleaned_data.get("aptitudes") or "").split(","):
            nombre = " ".join(parte.split())
            if nombre and nombre.casefold() not in vistos:
                if len(nombre) > 50:
                    raise ValidationError(_("Cada aptitud puede tener como máximo 50 caracteres."))
                vistos.add(nombre.casefold())
                nombres.append(nombre)
        if len(nombres) > MAX_APTITUDES:
            raise ValidationError(_("Puedes poner como máximo %(n)s aptitudes.") % {"n": MAX_APTITUDES})
        return nombres

    def guardar(self, perfil):
        aptitudes = []
        for nombre in self.cleaned_data["aptitudes"]:
            aptitud = Aptitud.objects.filter(nombre__iexact=nombre).first() or Aptitud.objects.create(nombre=nombre)
            aptitudes.append(aptitud)
        perfil.aptitudes.set(aptitudes)


class FormularioEnlaces(forms.ModelForm):
    """GitHub, LinkedIn y ORCID: se validan y se guardan en una sola forma (cuentas/perfiles.py)."""

    github = forms.CharField(label="GitHub", required=False, max_length=200, widget=forms.TextInput(attrs={"placeholder": "https://github.com/usuario"}),
                             help_text=_("Tu usuario o el enlace a tu perfil."))
    linkedin = forms.CharField(label="LinkedIn", required=False, max_length=200, widget=forms.TextInput(attrs={"placeholder": "https://www.linkedin.com/in/tu-nombre"}))
    orcid = forms.CharField(label="ORCID", required=False, max_length=40, widget=forms.TextInput(attrs={"placeholder": "0000-0000-0000-000X"}))

    class Meta:
        model = Perfil
        fields = ("github", "linkedin", "orcid")

    def clean_github(self):
        from cuentas.perfiles import normalizar_github

        return normalizar_github(self.cleaned_data.get("github"))

    def clean_linkedin(self):
        from cuentas.perfiles import normalizar_linkedin

        return normalizar_linkedin(self.cleaned_data.get("linkedin"))

    def clean_orcid(self):
        from cuentas.perfiles import normalizar_orcid

        return normalizar_orcid(self.cleaned_data.get("orcid"))


class FormularioAsignaturasImparte(forms.ModelForm):
    """Asignaturas que imparte un profesor, elegidas de la lista del plan de estudios (historia 3)."""

    class Meta:
        model = Perfil
        fields = ("asignaturas_imparte",)
        widgets = {"asignaturas_imparte": forms.SelectMultiple(attrs={"size": 10})}

    def __init__(self, *args, **kwargs):
        from proyectos.forms import configurar_selector_asignatura

        super().__init__(*args, **kwargs)
        actuales = list(self.instance.asignaturas_imparte.values_list("pk", flat=True)) if self.instance.pk else []
        configurar_selector_asignatura(self.fields["asignaturas_imparte"], conservar=actuales)
        self.fields["asignaturas_imparte"].required = False
        self.fields["asignaturas_imparte"].help_text = _("Mantén pulsada Ctrl (o Cmd) para elegir varias.")


class _FormularioConFechas(FormularioNFC, forms.ModelForm):
    """Inicio y fin por mes y año; "hasta hoy" deja el fin vacío."""

    inicio = CampoMes(label=_("Desde"))
    fin = CampoMes(label=_("Hasta"), required=False)
    campo_hasta_hoy = ""

    def clean(self):
        datos = super().clean()
        hasta_hoy = datos.get(self.campo_hasta_hoy)
        inicio, fin = datos.get("inicio"), datos.get("fin")
        if hasta_hoy:
            datos["fin"] = None
        elif not fin and "fin" not in self.errors:
            self.add_error("fin", _("Escribe la fecha de fin o marca la casilla."))
        elif inicio and fin and fin < inicio:
            self.add_error("fin", _("La fecha de fin no puede ser anterior a la de inicio."))
        return datos


class FormularioExperiencia(_FormularioConFechas):
    actualmente = forms.BooleanField(label=_("Actualmente trabajo aquí"), required=False)
    campo_hasta_hoy = "actualmente"

    class Meta:
        model = ExperienciaLaboral
        fields = ("cargo", "organizacion", "inicio", "fin", "descripcion")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 2, "maxlength": 300})}


class FormularioEstudio(_FormularioConFechas):
    en_curso = forms.BooleanField(label=_("En curso"), required=False)
    campo_hasta_hoy = "en_curso"

    class Meta:
        model = Estudio
        fields = ("institucion", "titulo", "inicio", "fin")


# --------------------------------------------------------------------------- Recuperar contraseña


class RecuperarContrasenaForm(PasswordResetForm):
    """El de Django, pero el correo sale con el logo UTEQ incrustado (config.correo.CorreoConLogo)."""

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email,
                  html_email_template_name=None):
        asunto = "".join(render_to_string(subject_template_name, context).splitlines())
        mensaje = CorreoConLogo(asunto, render_to_string(email_template_name, context), from_email, [to_email])
        if html_email_template_name is not None:
            mensaje.attach_alternative(render_to_string(html_email_template_name, context), "text/html")
        try:
            mensaje.send()
        except Exception:
            logger.exception("No se pudo enviar el correo de recuperación al usuario %s", context["user"].pk)


# --------------------------------------------------------------------------- Configuración inicial (spec 010)


def _campo_codigo():
    return forms.CharField(
        label=_("Código de configuración"), max_length=30, strip=True,
        help_text=_("12 caracteres, por ejemplo 7K4Q-M2XP-9WDA. Puedes escribirlo con o sin guiones."),
        widget=forms.TextInput(attrs={
            "autocomplete": "off", "autocapitalize": "characters", "spellcheck": "false",
            "autofocus": True, "placeholder": "XXXX-XXXX-XXXX", "class": "font-mono tracking-wider",
        }),
    )


class FormularioPrimerAdminNuevo(FormularioNFC, BaseUserCreationForm):
    """Configuración inicial, pestaña "Crear una cuenta nueva": código y datos del admin.

    Usa los validadores de contraseña de Django (BaseUserCreationForm). No avisa aquí si el correo
    ya existe: eso lo dice el servicio solo cuando el código es correcto, para que alguien sin
    código no pueda averiguar qué correos tienen cuenta.
    """

    codigo = _campo_codigo()

    class Meta:
        model = Usuario
        fields = ("nombres", "apellidos", "email")
        widgets = {
            "nombres": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "apellidos": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "nombre@correo.com"}),
        }

    field_order = ["codigo", "nombres", "apellidos", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.pop("autofocus", None)

    def clean_email(self):
        return UsuarioManager.normalizar_correo(self.cleaned_data.get("email"))

    def validate_unique(self):
        """Sin la validación de correo único del modelo (ver el docstring de la clase)."""


class FormularioPrimerAdminExistente(forms.Form):
    """Configuración inicial, pestaña "Usar una cuenta que ya existe": código, correo y contraseña."""

    codigo = _campo_codigo()
    email = forms.EmailField(
        label=_("Correo de la cuenta"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "nombre@correo.com"}),
    )
    password = forms.CharField(
        label=_("Contraseña de la cuenta"), strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
