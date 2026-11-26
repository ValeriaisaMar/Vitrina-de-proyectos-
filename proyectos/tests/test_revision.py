"""Pruebas de las pantallas de revisión: enviar, bandeja, empezar la revisión, decidir y correo."""

from unittest import mock

from django.contrib.admin.sites import site
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado, EventoEstado, Proyecto
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto, tomar


class BaseRevision(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora")
        self.profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR, nombres="Carla", apellidos="Vera")
        self.otro_profe = crear_usuario("profe2@correo.com", rol=Rol.PROFESOR)
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.proyecto = crear_proyecto(self.ana, coautores=[self.luis])

    def entrar(self, usuario):
        self.client.force_login(usuario)

    def enviado(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)

    def asignado(self, profesor=None):
        """Enviado y con revisor asignado, sin empezar ("Por revisar", spec 009)."""
        self.enviado()
        Proyecto.objects.filter(pk=self.proyecto.pk).update(revisor=profesor or self.profe)
        self.proyecto.refresh_from_db()

    def en_revision(self):
        self.enviado()
        tomar(self.proyecto, self.profe)

    def estado(self):
        self.proyecto.refresh_from_db()
        return self.proyecto.estado


class EnviarTests(BaseRevision):
    def url(self):
        return reverse("proyectos:enviar", args=[self.proyecto.slug])

    def test_un_autor_envia_con_mensaje(self):
        self.entrar(self.luis)
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        respuesta = self.client.post(self.url(), {"comentario": "Listo para revisar"})
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())
        self.assertEqual(self.estado(), Estado.ENVIADO)
        self.assertEqual(EventoEstado.objects.get().comentario, "Listo para revisar")

    def test_despues_de_enviar_no_se_edita_ni_se_elimina(self):
        self.enviado()
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse("proyectos:editar", args=[self.proyecto.slug])).status_code, 403)
        self.assertEqual(self.client.post(reverse("proyectos:eliminar", args=[self.proyecto.slug])).status_code, 403)
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_quien_no_es_autor_no_envia(self):
        for usuario in (crear_usuario("otra@correo.com"), self.profe):
            self.entrar(usuario)
            self.assertEqual(self.client.post(self.url()).status_code, 403)
        self.assertEqual(self.estado(), Estado.BORRADOR)

    def test_el_visitante_va_al_login(self):
        self.assertEqual(self.client.get(self.url()).status_code, 302)

    def test_mis_proyectos_ofrece_enviar(self):
        self.entrar(self.ana)
        self.assertContains(self.client.get(reverse("proyectos:mis_proyectos")), self.url())

    def test_reenvio_muestra_la_observacion(self):
        self.en_revision()
        cambiar_estado(self.proyecto, Estado.CON_OBSERVACIONES, self.profe, "Falta el manual de usuario")
        self.entrar(self.ana)
        respuesta = self.client.get(self.url())
        self.assertContains(respuesta, "Falta el manual de usuario")
        self.client.post(self.url(), {"comentario": "Agregué el manual"})
        self.assertEqual(self.estado(), Estado.ENVIADO)


class BandejaTests(BaseRevision):
    URL = reverse("proyectos:bandeja")

    def test_solo_docentes(self):
        self.assertEqual(self.client.get(self.URL).status_code, 302)
        self.entrar(self.ana)
        self.assertEqual(self.client.get(self.URL).status_code, 403)
        for usuario in (self.profe, self.admin):
            self.entrar(usuario)
            self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_por_revisar_muestra_solo_los_asignados(self):
        """Spec 009: cada profesor ve solo lo que tiene asignado; el admin ve todos los enviados."""
        crear_proyecto(self.ana, titulo="Borrador invisible")
        self.asignado()
        self.entrar(self.profe)
        respuesta = self.client.get(self.URL)
        self.assertEqual(list(respuesta.context["proyectos"]), [self.proyecto])
        self.assertNotContains(respuesta, "Borrador invisible")
        self.entrar(self.otro_profe)
        self.assertEqual(list(self.client.get(self.URL).context["proyectos"]), [])
        self.entrar(self.admin)
        self.assertEqual(list(self.client.get(self.URL).context["proyectos"]), [self.proyecto])

    def test_mis_revisiones_y_vista_del_admin(self):
        self.en_revision()
        self.entrar(self.otro_profe)
        self.assertEqual(list(self.client.get(self.URL, {"vista": "en_revision"}).context["proyectos"]), [])
        self.entrar(self.profe)
        self.assertEqual(list(self.client.get(self.URL, {"vista": "en_revision"}).context["proyectos"]), [self.proyecto])
        self.entrar(self.admin)
        self.assertEqual(list(self.client.get(self.URL, {"vista": "en_revision"}).context["proyectos"]), [self.proyecto])

    def test_decididos_por_mi(self):
        self.en_revision()
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe)
        self.entrar(self.profe)
        respuesta = self.client.get(self.URL, {"vista": "decididos"})
        self.assertEqual(list(respuesta.context["proyectos"]), [self.proyecto])
        self.assertEqual(respuesta.context["totales"], {"pendientes": 0, "en_revision": 0, "decididos": 1})

    def test_reenviado_se_marca(self):
        self.en_revision()
        cambiar_estado(self.proyecto, Estado.CON_OBSERVACIONES, self.profe, "Corrige")
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        self.entrar(self.profe)  # vuelve al mismo profesor (spec 009)
        respuesta = self.client.get(self.URL)
        self.assertContains(respuesta, "Reenviado")
        self.assertEqual(list(respuesta.context["proyectos"]), [self.proyecto])

    def test_vista_desconocida(self):
        self.entrar(self.profe)
        self.assertEqual(self.client.get(self.URL, {"vista": "<script>"}).context["vista"], "pendientes")


class TomarTests(BaseRevision):
    def url(self):
        return reverse("proyectos:tomar", args=[self.proyecto.slug])

    def test_tomar_lleva_a_la_revision(self):
        self.asignado()
        self.entrar(self.profe)
        respuesta = self.client.post(self.url())
        self.assertRedirects(respuesta, reverse("proyectos:revisar", args=[self.proyecto.slug]))
        self.assertEqual(self.estado(), Estado.EN_REVISION)
        self.assertEqual(self.proyecto.revisor, self.profe)

    def test_solo_por_post(self):
        self.enviado()
        self.entrar(self.profe)
        self.assertEqual(self.client.get(self.url()).status_code, 405)

    def test_si_otro_ya_lo_tomo_avisa(self):
        self.en_revision()
        self.entrar(self.otro_profe)
        respuesta = self.client.post(self.url(), follow=True)
        self.assertContains(respuesta, "El proyecto cambió de estado mientras tanto")
        self.assertEqual(self.proyecto.revisor, self.profe)

    def test_sin_ser_el_asignado_no_se_empieza(self):
        self.asignado(self.profe)
        self.entrar(self.otro_profe)
        self.assertEqual(self.client.post(self.url()).status_code, 403)
        self.entrar(self.admin)
        self.assertEqual(self.client.post(self.url()).status_code, 403)
        self.assertEqual(self.estado(), Estado.ENVIADO)

    def test_un_estudiante_no_toma(self):
        self.enviado()
        self.entrar(self.ana)
        self.assertEqual(self.client.post(self.url()).status_code, 403)


class DecidirTests(BaseRevision):
    def url(self):
        return reverse("proyectos:revisar", args=[self.proyecto.slug])

    def test_aprobar_publica_y_avisa_a_los_autores(self):
        self.en_revision()
        self.entrar(self.profe)
        respuesta = self.client.post(self.url(), {"decision": "aprobado", "comentario": "Excelente"})
        self.assertRedirects(respuesta, reverse("proyectos:bandeja") + "?vista=decididos")
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.estado, Estado.APROBADO)
        self.assertRegex(self.proyecto.codigo, r"^VP-\d{4}-0001$")
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(set(correo.to), {"ana@correo.com", "luis@correo.com"})
        self.assertIn("aprobado", correo.subject)
        self.assertIn(self.proyecto.codigo, correo.body)
        self.assertIn("Excelente", correo.body)
        self.client.logout()
        self.assertContains(self.client.get(reverse("vitrina:explorar")), self.proyecto.titulo)

    def test_pedir_cambios_sin_comentario(self):
        self.en_revision()
        self.entrar(self.profe)
        respuesta = self.client.post(self.url(), {"decision": "con_observaciones", "comentario": " "})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("comentario", respuesta.context["form"].errors)
        self.assertEqual(self.estado(), Estado.EN_REVISION)
        self.assertEqual(len(mail.outbox), 0)

    def test_rechazar_con_comentario(self):
        self.en_revision()
        self.entrar(self.profe)
        self.client.post(self.url(), {"decision": "rechazado", "comentario": "No es de la carrera"})
        self.assertEqual(self.estado(), Estado.RECHAZADO)
        self.assertIn("No es de la carrera", mail.outbox[0].body)

    def test_ni_otro_profesor_ni_el_admin_deciden(self):
        """Spec 009: solo el profesor asignado decide; el admin puede reasignar."""
        self.en_revision()
        for usuario in (self.otro_profe, self.admin):
            self.entrar(usuario)
            self.assertNotContains(self.client.get(self.url()), "Guardar decisión")
            self.assertEqual(self.client.post(self.url(), {"decision": "aprobado"}).status_code, 403)
        self.assertEqual(self.estado(), Estado.EN_REVISION)
        self.assertContains(self.client.get(self.url()), reverse("proyectos:reasignar", args=[self.proyecto.slug]))

    def test_si_el_correo_falla_la_decision_se_guarda(self):
        self.en_revision()
        self.entrar(self.profe)
        with mock.patch("proyectos.correos.CorreoConLogo.send", side_effect=OSError("sin red")):
            respuesta = self.client.post(self.url(), {"decision": "aprobado"}, follow=True)
        self.assertEqual(self.estado(), Estado.APROBADO)
        self.assertContains(respuesta, "no pudimos avisar a los autores")

    def test_un_borrador_no_se_revisa(self):
        self.entrar(self.profe)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_un_estudiante_no_entra_a_revisar(self):
        self.enviado()
        self.entrar(self.ana)
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_la_ficha_muestra_el_historial(self):
        self.en_revision()
        self.entrar(self.profe)
        respuesta = self.client.get(self.url())
        self.assertContains(respuesta, "empezó la revisión")
        self.assertContains(respuesta, "Guardar decisión")


class AdminTests(BaseRevision):
    def test_el_admin_no_cambia_estados_a_mano(self):
        from proyectos.admin import ProyectoAdmin

        peticion = RequestFactory().get("/")
        peticion.user = self.admin
        admin_proyecto = ProyectoAdmin(Proyecto, site)
        campos = admin_proyecto.get_readonly_fields(peticion, self.proyecto)
        for campo in ("estado", "revisor", "codigo", "aprobado_en"):
            self.assertIn(campo, campos)

    def test_el_historial_es_de_solo_lectura_y_no_se_borran_proyectos_enviados(self):
        from proyectos.admin import EventoEstadoAdmin, ProyectoAdmin

        self.enviado()
        peticion = RequestFactory().get("/")
        peticion.user = crear_usuario("root@correo.com", rol=Rol.ADMIN, is_staff=True, is_superuser=True)
        historial = EventoEstadoAdmin(EventoEstado, site)
        self.assertFalse(historial.has_change_permission(peticion))
        self.assertFalse(historial.has_delete_permission(peticion))
        self.assertFalse(ProyectoAdmin(Proyecto, site).has_delete_permission(peticion, self.proyecto))


class QuienDecideQuedaComoRevisorTests(BaseRevision):
    def test_la_verificacion_nombra_al_profesor_asignado(self):
        self.en_revision()
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe)
        respuesta = self.client.get(reverse("vitrina:verificar_codigo", args=[self.proyecto.codigo]))
        self.assertContains(respuesta, "Carla Vera")

    def test_si_decide_quien_lo_tomo_sigue_siendo_el(self):
        self.en_revision()
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.revisor, self.profe)
