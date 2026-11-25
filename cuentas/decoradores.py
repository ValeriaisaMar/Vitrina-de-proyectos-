"""Decoradores para proteger vistas según el rol (constitución, principio V)."""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles):
    """Deja pasar solo a usuarios con sesión y con alguno de los roles indicados.

    Uso:
        @rol_requerido("profesor", "admin")
        def bandeja_revision(request): ...

    - Sin sesión: redirige a iniciar sesión y, al entrar, vuelve a la página pedida.
    - Con sesión pero sin el rol: responde 403 ("No tienes permiso").

    Se compara con el ROL ACTIVO (spec 008): quien tiene los roles estudiante y admin pero está
    actuando como estudiante no entra a las páginas de admin hasta que cambie de rol.
    La comprobación ocurre en el servidor, así que conocer la URL no basta para entrar.
    """
    if not roles:
        raise ValueError("Indica al menos un rol, por ejemplo @rol_requerido('profesor').")

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.rol_activo not in roles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador
