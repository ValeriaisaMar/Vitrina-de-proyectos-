"""Rutas principales del proyecto.

Cada app define sus propias rutas en su archivo urls.py y aquí solo se incluyen.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Cambio de idioma: el selector ES/EN envía un POST a /i18n/setlang/
    path("i18n/", include("django.conf.urls.i18n")),
    # Temporal: inicio y cierre de sesión de Django. El módulo 002 lo reemplaza por la app cuentas.
    path("cuentas/", include("django.contrib.auth.urls")),
    path("", include("vitrina.urls")),
]

# En desarrollo, Django sirve los archivos que suben los usuarios.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
