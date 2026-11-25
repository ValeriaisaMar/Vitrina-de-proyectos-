"""Middleware propios del proyecto."""


class EspanolPorDefectoMiddleware:
    """Hace que la plataforma abra en español aunque el navegador esté en otro idioma.

    LocaleMiddleware de Django elige el idioma así: primero la cookie que deja el selector
    ES/EN y, si no hay cookie, el idioma del navegador (cabecera Accept-Language). La spec 001
    pide que un visitante nuevo vea siempre la versión en español, así que aquí se quita esa
    cabecera antes de que LocaleMiddleware la lea. Si la persona elige inglés, la cookie manda.

    Debe ir en MIDDLEWARE justo antes de LocaleMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META.pop("HTTP_ACCEPT_LANGUAGE", None)
        return self.get_response(request)


class RolActivoMiddleware:
    """Fija en cada petición el rol con el que actúa la persona: request.user.rol_activo (spec 008).

    El rol activo se guarda en la sesión. Antes de usarlo se comprueba que la persona todavía lo
    tenga: si alguien manipula la sesión con un rol ajeno, o un admin le quitó el rol que tenía
    activo, se ignora y se usa su rol por defecto (el último que usó o el de menor privilegio).

    Debe ir en MIDDLEWARE después de AuthenticationMiddleware (necesita request.user).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from cuentas.roles import CLAVE_SESION  # import local: este módulo se carga antes que las apps

        usuario = request.user
        if usuario.is_authenticated:
            guardado = request.session.get(CLAVE_SESION)
            if guardado and usuario.tiene_rol(guardado):
                usuario.rol_activo = guardado
            else:
                usuario.rol_activo = usuario.rol_por_defecto()
                request.session[CLAVE_SESION] = usuario.rol_activo
        return self.get_response(request)
