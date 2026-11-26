"""Rutas principales del proyecto.

Cada app define sus propias rutas en su archivo urls.py y aquí solo se incluyen.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from cuentas.views import configuracion_inicial

urlpatterns = [
    path("admin/", admin.site.urls),
    # Cambio de idioma: el selector ES/EN envía un POST a /i18n/setlang/
    path("i18n/", include("django.conf.urls.i18n")),
    # Registro, activación, inicio de sesión, recuperación y perfil (módulo 002)
    path("cuentas/", include("cuentas.urls")),
    # Crear el primer admin desde el navegador; solo existe mientras no hay un admin (spec 010)
    path("configuracion-inicial/", configuracion_inicial, name="configuracion_inicial"),
    # Proyectos de los estudiantes: mis proyectos, crear, editar y eliminar (módulo 003)
    path("proyectos/", include("proyectos.urls")),
    path("comunidad/", include("comunidad.urls")),
    path("", include("vitrina.urls")),
]

# En desarrollo, Django sirve los archivos que suben los usuarios.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
