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

    def _crear(self, email, password, **campos):
        if not email:
            raise ValueError("El correo es obligatorio.")
        usuario = self.model(email=self.normalizar_correo(email), **campos)
        usuario.set_password(password)  # guarda la contraseña cifrada, nunca en texto plano
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **campos):
        """Crea una cuenta normal. El rol por defecto es estudiante."""
        campos.setdefault("is_staff", False)
        campos.setdefault("is_superuser", False)
        return self._crear(email, password, **campos)

    def create_superuser(self, email, password=None, **campos):
        """Crea un administrador con acceso al panel de Django y rol admin."""
        from cuentas.models import Rol  # import local para evitar un ciclo

        campos.setdefault("is_staff", True)
        campos.setdefault("is_superuser", True)
        campos.setdefault("is_active", True)
        campos.setdefault("rol", Rol.ADMIN)
        if not campos["is_staff"] or not campos["is_superuser"]:
            raise ValueError("Un superusuario debe tener is_staff e is_superuser en True.")
        return self._crear(email, password, **campos)
