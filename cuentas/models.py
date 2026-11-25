"""Modelos de la app cuentas.

Se usa un usuario propio (no el que trae Django) para que:
- se inicie sesión con el correo, que es único y sin distinguir mayúsculas;
- cada persona tenga uno o varios roles (estudiante, profesor, admin) y elija con cuál entra;
- los campos queden en español, como pide la constitución.

Roles (spec 008): una persona puede tener varios roles a la vez (RolAsignado) y actúa con uno
solo, el "rol activo", que vive en la sesión. Lo que ve y puede hacer depende del rol activo,
no de todos sus roles juntos. Cada vez que se da o se quita un rol queda en CambioRol.
"""

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cuentas.managers import UsuarioManager


class Rol(models.TextChoices):
    """Roles con cuenta. El visitante no tiene cuenta, por eso no aparece aquí."""

    ESTUDIANTE = "estudiante", _("Estudiante")
    PROFESOR = "profesor", _("Profesor")
    ADMIN = "admin", _("Admin")


# De menor a mayor privilegio. Sirve para ordenar los roles y para elegir el rol por defecto.
JERARQUIA = (Rol.ESTUDIANTE, Rol.PROFESOR, Rol.ADMIN)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Persona con cuenta en la plataforma."""

    email = models.EmailField(_("correo electrónico"), unique=True)
    nombres = models.CharField(_("nombres"), max_length=80)
    apellidos = models.CharField(_("apellidos"), max_length=80)
    # El último rol con el que entró: al iniciar sesión se vuelve a usar si todavía lo tiene.
    ultimo_rol = models.CharField(_("último rol usado"), max_length=12, choices=Rol.choices, blank=True)

    # is_active queda en False hasta que la persona abre el enlace de activación (módulo 002).
    is_active = models.BooleanField(_("activo"), default=False)
    is_staff = models.BooleanField(_("acceso al panel de Django"), default=False)
    fecha_registro = models.DateTimeField(_("fecha de registro"), default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"  # el campo con el que se inicia sesión
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nombres", "apellidos"]  # los pide createsuperuser

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return self.nombre_completo or self.email

    def save(self, *args, **kwargs):
        """Guarda siempre el correo en minúsculas para que sea único sin importar mayúsculas."""
        self.email = UsuarioManager.normalizar_correo(self.email)
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def get_full_name(self):
        return self.nombre_completo

    def get_short_name(self):
        return self.nombres

    # ------------------------------------------------------------------ Roles que TIENE

    @property
    def roles(self):
        """Los roles que tiene, de menor a mayor privilegio. Ej.: ["estudiante", "admin"].

        Usa roles_asignados.all(): si la consulta trae prefetch_related("roles_asignados"),
        no hace consultas extra. El resultado se guarda en el objeto durante la petición.
        """
        if not hasattr(self, "_roles"):
            if self.pk is None:
                return []
            tiene = {asignado.rol for asignado in self.roles_asignados.all()}
            self._roles = [rol.value for rol in JERARQUIA if rol in tiene]
        return self._roles

    def olvidar_roles(self):
        """Borra la lista guardada en memoria (después de dar o quitar un rol)."""
        self.__dict__.pop("_roles", None)
        if hasattr(self, "_prefetched_objects_cache"):
            self._prefetched_objects_cache.pop("roles_asignados", None)

    def tiene_rol(self, rol):
        """True si la persona tiene ese rol (aunque ahora esté actuando con otro)."""
        return rol in self.roles

    def rol_por_defecto(self):
        """El último rol con el que entró, si todavía lo tiene; si no, el de menor privilegio."""
        if self.ultimo_rol and self.tiene_rol(self.ultimo_rol):
            return self.ultimo_rol
        return self.roles[0] if self.roles else Rol.ESTUDIANTE.value

    # ------------------------------------------------------------------ Rol con el que ACTÚA

    @property
    def rol_activo(self):
        """El rol con el que está actuando. En una petición lo fija config.middleware.RolActivoMiddleware.

        Fuera de una petición (correos, comandos, pruebas de servicios) es el rol por defecto.
        """
        return getattr(self, "_rol_activo", None) or self.rol_por_defecto()

    @rol_activo.setter
    def rol_activo(self, rol):
        self._rol_activo = rol

    def get_rol_activo_display(self):
        return Rol(self.rol_activo).label

    @property
    def es_estudiante(self):
        return self.rol_activo == Rol.ESTUDIANTE

    @property
    def es_profesor(self):
        return self.rol_activo == Rol.PROFESOR

    @property
    def es_admin(self):
        return self.rol_activo == Rol.ADMIN

    @property
    def es_docente(self):
        """Actúa como profesor o como admin: los dos pueden revisar proyectos."""
        return self.rol_activo in (Rol.PROFESOR, Rol.ADMIN)


class RolAsignado(models.Model):
    """Un rol que tiene una persona. Una fila por rol; nunca dos veces el mismo."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roles_asignados", verbose_name=_("usuario"))
    rol = models.CharField(_("rol"), max_length=12, choices=Rol.choices)
    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name=_("asignado por"),
    )
    asignado_en = models.DateTimeField(_("asignado en"), default=timezone.now)

    class Meta:
        verbose_name = _("rol asignado")
        verbose_name_plural = _("roles asignados")
        ordering = ["asignado_en", "id"]
        constraints = [models.UniqueConstraint(fields=["usuario", "rol"], name="un_rol_por_persona")]

    def __str__(self):
        return f"{self.usuario} · {self.get_rol_display()}"


class CambioRol(models.Model):
    """Registro de cada rol que se dio o se quitó: a quién, cuál, quién lo hizo y cuándo."""

    class Accion(models.TextChoices):
        AGREGADO = "agregado", _("agregado")
        QUITADO = "quitado", _("quitado")

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cambios_de_rol", verbose_name=_("usuario"))
    rol = models.CharField(_("rol"), max_length=12, choices=Rol.choices)
    accion = models.CharField(_("acción"), max_length=10, choices=Accion.choices)
    hecho_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name=_("hecho por"),
    )
    fecha = models.DateTimeField(_("fecha"), default=timezone.now)

    class Meta:
        verbose_name = _("cambio de rol")
        verbose_name_plural = _("cambios de rol")
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.usuario} · {self.get_rol_display()} {self.get_accion_display()}"


# --------------------------------------------------------------------------- Correo de envío (spec 008, historia 3)


class Seguridad(models.TextChoices):
    STARTTLS = "starttls", _("STARTTLS")
    SSL = "ssl", _("SSL/TLS")
    NINGUNA = "ninguna", _("Ninguna")


CLAVE_CACHE_CORREO = "configuracion_correo"


class ConfiguracionCorreo(models.Model):
    """Cuenta de correo desde la que la plataforma envía sus mensajes. Hay una sola fila (singleton).

    La contraseña de aplicación se guarda cifrada con Fernet (cuentas/cifrado.py) y nunca se vuelve
    a mostrar. Si esta fila no existe, el correo sigue saliendo como siempre: con los datos del .env.
    """

    servidor = models.CharField(_("servidor SMTP"), max_length=120)
    puerto = models.PositiveIntegerField(_("puerto"), default=587)
    seguridad = models.CharField(_("seguridad"), max_length=10, choices=Seguridad.choices, default=Seguridad.STARTTLS)
    usuario = models.CharField(_("usuario o correo de acceso"), max_length=254)
    clave_cifrada = models.TextField(_("contraseña cifrada"), blank=True, editable=False)
    nombre_remitente = models.CharField(_("nombre del remitente"), max_length=80, default="Vitrina de Proyectos UTEQ")
    correo_remitente = models.EmailField(_("correo del remitente"), blank=True)

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name=_("actualizado por"),
    )
    actualizado_en = models.DateTimeField(_("actualizado en"), auto_now=True)

    ultima_prueba_en = models.DateTimeField(_("última prueba"), null=True, blank=True)
    ultima_prueba_ok = models.BooleanField(_("última prueba correcta"), null=True, blank=True)
    ultima_prueba_mensaje = models.CharField(_("resultado de la última prueba"), max_length=300, blank=True)

    class Meta:
        verbose_name = _("configuración de correo")
        verbose_name_plural = _("configuración de correo")

    def __str__(self):
        return f"{self.usuario} · {self.servidor}:{self.puerto}"

    def save(self, *args, **kwargs):
        self.pk = 1  # siempre la misma fila
        super().save(*args, **kwargs)
        cache.delete(CLAVE_CACHE_CORREO)  # el backend vuelve a leer la configuración nueva

    def delete(self, *args, **kwargs):
        resultado = super().delete(*args, **kwargs)
        cache.delete(CLAVE_CACHE_CORREO)
        return resultado

    @classmethod
    def actual(cls):
        """La configuración guardada, o None si el admin todavía no la ha creado."""
        return cls.objects.filter(pk=1).select_related("actualizado_por").first()

    @property
    def tiene_clave(self):
        return bool(self.clave_cifrada)

    @property
    def remitente(self):
        return self.correo_remitente or self.usuario
