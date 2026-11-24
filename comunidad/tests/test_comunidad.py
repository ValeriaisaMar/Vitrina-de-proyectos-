"""Pruebas de comunidad (módulo 007): me gusta, favoritos, comentarios y moderación."""

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from comunidad.models import Comentario, Favorito, MeGusta
from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto


class BaseComunidad(TestCase):
    def setUp(self):
        cache.clear()  # el límite de comentarios vive en la caché
        self.ana = crear_usuario("ana@correo.com")
        self.luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora")
        self.visita = crear_usuario("visita@correo.com", nombres="Sofía", apellidos="Ríos")
        self.profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.proyecto = crear_proyecto(self.ana, titulo="Gestor de tutorías", coautores=[self.luis])
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        cambiar_estado(self.proyecto, Estado.EN_REVISION, self.profe)
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe)

    def url(self, nombre, *args):
        return reverse(f"comunidad:{nombre}", args=args or [self.proyecto.slug])

    def comentar(self, usuario, texto="Muy buen proyecto"):
        self.client.force_login(usuario)
        return self.client.post(self.url("comentar"), {"texto": texto})


class MeGustaTests(BaseComunidad):
    def test_dar_y_quitar(self):
        self.client.force_login(self.visita)
        respuesta = self.client.post(self.url("me_gusta"))
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url() + "#comunidad", fetch_redirect_response=False)
        self.assertEqual(MeGusta.objects.count(), 1)
        self.client.post(self.url("me_gusta"))
        self.assertEqual(MeGusta.objects.count(), 0)

    def test_un_autor_no_se_da_me_gusta(self):
        self.client.force_login(self.luis)
        self.client.post(self.url("me_gusta"))
        self.assertFalse(MeGusta.objects.exists())

    def test_visitante_va_al_login_y_get_no_vale(self):
        self.assertEqual(self.client.post(self.url("me_gusta")).status_code, 302)
        self.client.force_login(self.visita)
        self.assertEqual(self.client.get(self.url("me_gusta")).status_code, 405)

    def test_solo_proyectos_aprobados(self):
        borrador = crear_proyecto(self.ana, titulo="Borrador")
        self.client.force_login(self.visita)
        for nombre in ("me_gusta", "favorito", "comentar"):
            self.assertEqual(self.client.post(reverse(f"comunidad:{nombre}", args=[borrador.slug])).status_code, 404)

    def test_la_ficha_muestra_el_total(self):
        MeGusta.objects.create(usuario=self.visita, proyecto=self.proyecto)
        MeGusta.objects.create(usuario=self.profe, proyecto=self.proyecto)
        self.assertContains(self.client.get(self.proyecto.get_absolute_url()), "2 me gusta")


class FavoritosTests(BaseComunidad):
    def test_guardar_ver_y_quitar(self):
        self.client.force_login(self.visita)
        self.client.post(self.url("favorito"))
        self.assertContains(self.client.get(reverse("comunidad:favoritos")), "Gestor de tutorías")
        respuesta = self.client.post(self.url("favorito"), {"volver": "favoritos"})
        self.assertRedirects(respuesta, reverse("comunidad:favoritos"))
        self.assertFalse(Favorito.objects.exists())

    def test_son_privados(self):
        Favorito.objects.create(usuario=self.visita, proyecto=self.proyecto)
        self.client.force_login(self.profe)
        self.assertNotContains(self.client.get(reverse("comunidad:favoritos")), "Gestor de tutorías")

    def test_sin_sesion_va_al_login(self):
        self.assertEqual(self.client.get(reverse("comunidad:favoritos")).status_code, 302)


class ComentariosTests(BaseComunidad):
    def test_publicar(self):
        respuesta = self.comentar(self.visita, "  Me sirvió para mi tesis  ")
        comentario = Comentario.objects.get()
        self.assertEqual(comentario.texto, "Me sirvió para mi tesis")
        self.assertRedirects(respuesta, f"{self.proyecto.get_absolute_url()}#comentario-{comentario.pk}", fetch_redirect_response=False)
        self.client.logout()
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(respuesta, "Me sirvió para mi tesis")
        self.assertContains(respuesta, "Sofía Ríos")

    def test_vacio_o_largo(self):
        self.comentar(self.visita, " a ")
        self.comentar(self.visita, "x" * 1001)
        self.assertFalse(Comentario.objects.exists())

    def test_el_html_se_escapa(self):
        self.comentar(self.visita, "<script>alert('hola')</script>")
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(respuesta, "&lt;script&gt;alert(&#x27;hola&#x27;)&lt;/script&gt;")
        self.assertNotContains(respuesta, "<script>alert(")

    def test_limite_de_cinco_cada_diez_minutos(self):
        for i in range(6):
            self.comentar(self.visita, f"Comentario número {i}")
        self.assertEqual(Comentario.objects.count(), 5)

    def test_el_autor_del_comentario_lo_borra_y_nadie_mas(self):
        self.comentar(self.visita)
        comentario = Comentario.objects.get()
        self.client.force_login(self.ana)  # autora del proyecto, pero no del comentario
        self.assertEqual(self.client.post(self.url("borrar", comentario.pk)).status_code, 403)
        self.client.force_login(self.visita)
        self.client.post(self.url("borrar", comentario.pk))
        self.assertFalse(Comentario.objects.exists())


class ModeracionTests(BaseComunidad):
    def setUp(self):
        super().setUp()
        self.comentar(self.visita, "Comentario fuera de lugar")
        self.comentario = Comentario.objects.get()

    def test_un_coautor_oculta_y_el_publico_no_lo_ve(self):
        self.client.force_login(self.luis)
        self.client.post(self.url("ocultar", self.comentario.pk))
        self.comentario.refresh_from_db()
        self.assertTrue(self.comentario.oculto)
        self.assertEqual(self.comentario.ocultado_por, self.luis)
        self.assertContains(self.client.get(self.proyecto.get_absolute_url()), "Oculto")
        self.client.logout()
        self.assertNotContains(self.client.get(self.proyecto.get_absolute_url()), "Comentario fuera de lugar")

    def test_el_admin_oculta_y_vuelve_a_mostrar(self):
        self.client.force_login(self.admin)
        self.client.post(self.url("ocultar", self.comentario.pk))
        self.client.post(self.url("ocultar", self.comentario.pk))
        self.comentario.refresh_from_db()
        self.assertFalse(self.comentario.oculto)
        self.assertIsNone(self.comentario.ocultado_por)

    def test_otros_no_moderan(self):
        for usuario in (self.visita, self.profe):
            self.client.force_login(usuario)
            self.assertEqual(self.client.post(self.url("ocultar", self.comentario.pk)).status_code, 403)
        self.comentario.refresh_from_db()
        self.assertFalse(self.comentario.oculto)
