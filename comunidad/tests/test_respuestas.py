"""Spec 008, historia 4: etiqueta de autor en los comentarios y respuestas de los autores."""

from django.core import mail
from django.core.exceptions import ValidationError
from django.urls import reverse

from comunidad.models import Comentario
from comunidad.tests.test_comunidad import BaseComunidad


class RespuestasTests(BaseComunidad):
    def setUp(self):
        super().setUp()
        self.comentario = Comentario.objects.create(proyecto=self.proyecto, autor=self.visita, texto="¿Usaron Django?")

    def responder(self, usuario, comentario=None, texto="Sí, con Django 6"):
        self.client.force_login(usuario)
        return self.client.post(reverse("comunidad:responder", args=[(comentario or self.comentario).pk]), {"texto": texto})

    def test_un_autor_responde_y_se_avisa_por_correo(self):
        respuesta = self.responder(self.luis)  # coautor
        nueva = Comentario.objects.get(respuesta_a=self.comentario)
        self.assertRedirects(respuesta, f"{self.proyecto.get_absolute_url()}#comentario-{nueva.pk}", fetch_redirect_response=False)
        self.assertEqual(nueva.autor, self.luis)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.visita.email])
        self.assertIn("Sí, con Django 6", mail.outbox[0].body)

    def test_solo_los_autores_responden(self):
        for usuario in (self.visita, self.profe, self.admin):
            self.assertEqual(self.responder(usuario).status_code, 403)
        self.assertFalse(Comentario.objects.filter(respuesta_a=self.comentario).exists())
        self.client.logout()
        self.assertEqual(self.client.post(reverse("comunidad:responder", args=[self.comentario.pk]), {"texto": "x"}).status_code, 302)

    def test_no_hay_segundo_nivel(self):
        self.responder(self.ana)
        primera = Comentario.objects.get(respuesta_a=self.comentario)
        self.assertEqual(self.responder(self.luis, comentario=primera).status_code, 403)
        hija = Comentario(proyecto=self.proyecto, autor=self.ana, texto="otra", respuesta_a=primera)
        with self.assertRaises(ValidationError):
            hija.full_clean()

    def test_la_respuesta_sale_debajo_con_la_etiqueta_autor(self):
        self.responder(self.ana)
        pagina = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(pagina, "insignia-autor")
        self.assertContains(pagina, "Sí, con Django 6")
        self.assertContains(pagina, "Comentarios (2)")
        comentarios = pagina.context["comunidad"]["comentarios"]
        self.assertEqual(len(comentarios), 1)  # la respuesta no se repite como comentario suelto
        self.assertEqual([r.texto for r in comentarios[0].hilo], ["Sí, con Django 6"])

    def test_el_boton_responder_solo_lo_ven_los_autores(self):
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(self.proyecto.get_absolute_url()), "Publicar respuesta")
        self.client.force_login(self.visita)
        self.assertNotContains(self.client.get(self.proyecto.get_absolute_url()), "Publicar respuesta")

    def test_ocultar_el_comentario_oculta_su_hilo(self):
        self.responder(self.ana)
        self.client.force_login(self.ana)
        self.client.post(reverse("comunidad:ocultar", args=[self.comentario.pk]))
        self.client.force_login(self.visita)
        pagina = self.client.get(self.proyecto.get_absolute_url())
        self.assertNotContains(pagina, "Sí, con Django 6")
        self.assertNotContains(pagina, "¿Usaron Django?")
        self.assertTrue(Comentario.objects.filter(respuesta_a=self.comentario).exists())  # ocultar no borra

    def test_no_se_responde_un_comentario_oculto(self):
        self.comentario.oculto = True
        self.comentario.save()
        self.assertEqual(self.responder(self.ana).status_code, 403)

    def test_comentario_de_autor_destacado_y_etiqueta_de_docente_revisor(self):
        Comentario.objects.create(proyecto=self.proyecto, autor=self.ana, texto="Gracias por mirar")
        Comentario.objects.create(proyecto=self.proyecto, autor=self.profe, texto="Buen trabajo")
        pagina = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(pagina, "border-l-8", count=1)
        self.assertContains(pagina, "Docente revisor", count=1)

    def test_sin_consultas_extra_por_comentario(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from comunidad.consultas import datos_comunidad

        def contar():
            self.visita.olvidar_roles()
            with CaptureQueriesContext(connection) as consultas:
                for comentario in datos_comunidad(self.visita, self.proyecto)["comentarios"]:
                    [r.autor.nombre_completo for r in comentario.hilo]
            return len(consultas)

        # La medida base ya incluye una respuesta: la consulta que precarga los roles de quien
        # responde (para enlazar su perfil, spec 009) solo corre si hay respuestas.
        base = Comentario.objects.create(proyecto=self.proyecto, autor=self.visita, texto="Pregunta base")
        Comentario.objects.create(proyecto=self.proyecto, autor=self.ana, texto="Respuesta base", respuesta_a=base)
        con_uno = contar()
        for i in range(5):
            padre = Comentario.objects.create(proyecto=self.proyecto, autor=self.visita, texto=f"Pregunta {i}")
            Comentario.objects.create(proyecto=self.proyecto, autor=self.ana, texto=f"Respuesta {i}", respuesta_a=padre)
        self.assertEqual(contar(), con_uno)  # más comentarios, mismas consultas
