"""Gestor del modelo Usuario: cómo se crean usuarios y cómo se buscan al iniciar sesión."""

from django.contrib.auth.base_user import BaseUserManager


class UsuarioManager(BaseUserManager):
    """Crea usuarios identificados por correo en lugar de un nombre de usuario."""

    use_in_migrations = True

    @staticmethod
    def normalizar_correo(email):
        """Quita espacios y pasa el correo completo a minúsculas.

        Django solo pone en minúsculas el dominio; nosotros lo hacemos con todo el correo
        para que Ana@Correo.com y ana@correo.com sean la misma cuenta.
        """
        return (email or "").strip().lower()

    def get_by_natural_key(self, email):
        """Busca al usuario sin distinguir mayúsculas. La usa el inicio de sesión."""
        return self.get(email__iexact=self.normalizar_correo(email))

    def _crear(self, email, password, roles, **campos):
        from cuentas.models import RolAsignado  # import local para evitar un ciclo

        if not email:
            raise ValueError("El correo es obligatorio.")
        usuario = self.model(email=self.normalizar_correo(email), **campos)
        usuario.set_password(password)  # guarda la contraseña cifrada, nunca en texto plano
        usuario.save(using=self._db)
        # Todo usuario tiene al menos un rol (spec 008)
        for rol in dict.fromkeys(roles):  # sin repetidos, en el orden dado
            RolAsignado.objects.using(self._db).create(usuario=usuario, rol=rol)
        usuario.olvidar_roles()
        return usuario

    def create_user(self, email, password=None, rol=None, roles=None, **campos):
        """Crea una cuenta normal. Por defecto con el rol estudiante.

        Acepta un rol (rol="profesor") o varios (roles=["estudiante", "admin"]).
        """
        campos.setdefault("is_staff", False)
        campos.setdefault("is_superuser", False)
        return self._crear(email, password, roles or [rol or "estudiante"], **campos)

    def create_superuser(self, email, password=None, rol=None, roles=None, **campos):
        """Crea un administrador con acceso al panel de Django y el rol admin."""
        campos.setdefault("is_staff", True)
        campos.setdefault("is_superuser", True)
        campos.setdefault("is_active", True)
        if not campos["is_staff"] or not campos["is_superuser"]:
            raise ValueError("Un superusuario debe tener is_staff e is_superuser en True.")
        usuario = self._crear(email, password, roles or [rol or "admin"], **campos)
        # Spec 010: queda "Configuración inicial" en el registro de roles y el código pendiente
        # de la configuración inicial deja de servir (import local para evitar un ciclo).
        from cuentas.configuracion_inicial import al_crear_superusuario

        al_crear_superusuario(usuario)
        return usuario
