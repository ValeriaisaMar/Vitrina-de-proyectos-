"""Historia 5: páginas protegidas por rol con @rol_requerido."""

from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import include, path

from cuentas.decoradores import rol_requerido
from cuentas.tests.utilidades import crear_usuario


@rol_requerido("profesor", "admin")
def solo_revisores(request):
    return HttpResponse("zona de revisión")


urlpatterns = [
    path("revision/", solo_revisores),
    path("i18n/", include("django.conf.urls.i18n")),
    path("cuentas/", include("cuentas.urls")),
    path("proyectos/", include("proyectos.urls")),
    path("comunidad/", include("comunidad.urls")),
    path("", include("vitrina.urls")),
]


@override_settings(ROOT_URLCONF=__name__)
class RolRequeridoTests(TestCase):
    def test_visitante_va_a_iniciar_sesion_y_luego_vuelve(self):
        respuesta = self.client.get("/revision/")
        self.assertRedirects(respuesta, "/cuentas/entrar/?next=/revision/", fetch_redirect_response=False)

    def test_estudiante_recibe_403_con_el_diseno(self):
        self.client.force_login(crear_usuario(rol="estudiante"))
        respuesta = self.client.get("/revision/")
        self.assertEqual(respuesta.status_code, 403)
        self.assertTemplateUsed(respuesta, "403.html")
        self.assertContains(respuesta, "No tienes permiso", status_code=403)

    def test_profesor_y_admin_entran(self):
        for rol in ("profesor", "admin"):
            self.client.force_login(crear_usuario(email=f"{rol}@uteq.edu.ec", rol=rol))
            self.assertContains(self.client.get("/revision/"), "zona de revisión")

    def test_sin_roles_es_un_error_de_programacion(self):
        with self.assertRaises(ValueError):
            rol_requerido()
