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
