"""Spec 009, historia 5: el estudiante elige al profesor que revisa su proyecto."""

from datetime import timedelta

from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from cuentas.models import Aptitud, Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos import solicitudes
from proyectos.models import AccionEvento, Asignatura, Estado, EstadoSolicitud, EventoEstado, Proyecto, SolicitudRevision, Tecnologia
from proyectos.servicios import cambiar_estado
from proyectos.tests.utilidades import crear_proyecto


class BaseSolicitudes(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com", nombres="Ana", apellidos="Paz")
        self.luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora")
        self.rosa = crear_usuario("rosa@correo.com", nombres="Rosa", apellidos="Vera", rol=Rol.PROFESOR)
        self.pablo = crear_usuario("pablo@correo.com", nombres="Pablo", apellidos="Ríos", rol=Rol.PROFESOR)
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.asignatura = Asignatura.objects.order_by("pk").first()
        self.proyecto = crear_proyecto(self.ana, coautores=[self.luis], asignatura=self.asignatura)

    def enviar(self, profesor=None):
        """El creador envía y elige profesor (o lo deja "Por asignar")."""
        return solicitudes.enviar(self.proyecto, self.ana, "", profesor)

    def recargar(self):
        self.proyecto.refresh_from_db()
        return self.proyecto


class ElegirAlEnviarTests(BaseSolicitudes):
    URL = None

    def url(self):
        return reverse("proyectos:enviar", args=[self.proyecto.slug])

    def test_el_creador_elige_y_el_profesor_recibe_un_correo(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.url())
        self.assertContains(respuesta, "Elige quién revisa tu proyecto")
        self.assertContains(respuesta, "Rosa Vera")
        respuesta = self.client.post(self.url(), {"comentario": "", "profesor": self.rosa.pk})
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())
        proyecto = self.recargar()
        self.assertEqual((proyecto.estado, proyecto.subestado), (Estado.ENVIADO, "esperando"))
        self.assertEqual(proyecto.solicitud_pendiente.profesor, self.rosa)
        self.assertEqual([c.to for c in mail.outbox], [["rosa@correo.com"]])

    def test_sin_elegir_no_se_envia(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(self.url(), {"comentario": ""})
        self.assertContains(respuesta, "Elige quién revisará tu proyecto")
        self.assertEqual(self.recargar().estado, Estado.BORRADOR)

    def test_el_coautor_envia_pero_no_elige(self):
        self.client.force_login(self.luis)
        self.assertNotContains(self.client.get(self.url()), "Elige quién revisa tu proyecto")
        self.client.post(self.url(), {"comentario": "", "profesor": self.rosa.pk})
        proyecto = self.recargar()
        self.assertEqual(proyecto.subestado, "por_asignar")
        self.assertFalse(SolicitudRevision.objects.exists())
        self.client.force_login(self.luis)
        self.assertEqual(self.client.get(reverse("proyectos:elegir_revisor", args=[proyecto.slug])).status_code, 403)
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(reverse("vitrina:panel")), reverse("proyectos:elegir_revisor", args=[proyecto.slug]))


class ExclusionesTests(BaseSolicitudes):
    def test_nunca_aparecen_los_autores(self):
        profe_autor = crear_usuario("autora@correo.com", nombres="Autora", roles=["estudiante", "profesor"])
        proyecto = crear_proyecto(self.ana, titulo="Con profe autora", coautores=[profe_autor])
        ids = [p.pk for p in solicitudes.profesores(excluir_autores_de=proyecto)]
        self.assertNotIn(profe_autor.pk, ids)
        self.assertIn(self.rosa.pk, ids)

    def test_no_disponible_sale_en_la_lista_pero_no_se_elige(self):
        self.rosa.perfil.recibiendo_proyectos = False
        self.rosa.perfil.save()
        self.rosa.perfil.asignaturas_imparte.add(self.asignatura)
        self.assertEqual(solicitudes.sugerir_profesores(self.proyecto), [])
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse("proyectos:enviar", args=[self.proyecto.slug]))
        self.assertContains(respuesta, "No está recibiendo proyectos")
        self.client.post(reverse("proyectos:enviar", args=[self.proyecto.slug]), {"comentario": "", "profesor": self.rosa.pk})
        self.assertEqual(self.recargar().estado, Estado.BORRADOR)
        with self.assertRaises(ValidationError):
            cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
            solicitudes.solicitar(self.recargar(), self.rosa, self.ana)

    def test_quien_ya_rechazo_no_se_sugiere_pero_se_puede_elegir(self):
        self.rosa.perfil.asignaturas_imparte.add(self.asignatura)
        solicitud = self.enviar(self.rosa)
        solicitudes.no_aceptar(solicitud, self.rosa)
        self.assertEqual(solicitudes.sugerir_profesores(self.recargar()), [])
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse("proyectos:elegir_revisor", args=[self.proyecto.slug]))
        self.assertContains(respuesta, "Ya rechazó este proyecto")
        solicitudes.solicitar(self.proyecto, self.rosa, self.ana)  # se puede volver a elegir
        self.assertEqual(self.recargar().subestado, "esperando")


class AceptarYNoAceptarTests(BaseSolicitudes):
    def test_aceptar_lo_pone_en_revision_y_avisa_a_los_autores(self):
        solicitud = self.enviar(self.rosa)
        self.client.force_login(self.rosa)
        self.assertContains(self.client.get(reverse("proyectos:solicitudes")), self.proyecto.titulo)
        mail.outbox.clear()
        respuesta = self.client.post(reverse("proyectos:aceptar_solicitud", args=[solicitud.pk]))
        self.assertRedirects(respuesta, reverse("proyectos:revisar", args=[self.proyecto.slug]))
        proyecto = self.recargar()
        self.assertEqual((proyecto.estado, proyecto.revisor), (Estado.EN_REVISION, self.rosa))
        self.assertEqual(set(mail.outbox[0].to), {"ana@correo.com", "luis@correo.com"})
        self.assertTrue(EventoEstado.objects.filter(proyecto=proyecto, accion=AccionEvento.ACEPTADA, estado_nuevo=Estado.EN_REVISION).exists())

    def test_solo_el_profesor_de_la_solicitud_responde(self):
        solicitud = self.enviar(self.rosa)
        self.client.force_login(self.pablo)
        self.assertEqual(self.client.post(reverse("proyectos:aceptar_solicitud", args=[solicitud.pk])).status_code, 404)
        with self.assertRaises(PermissionDenied):
            solicitudes.aceptar(solicitud, self.pablo)

    def test_no_aceptar_sin_mensaje(self):
        solicitud = self.enviar(self.rosa)
        mail.outbox.clear()
        self.client.force_login(self.rosa)
        self.client.post(reverse("proyectos:no_aceptar_solicitud", args=[solicitud.pk]), {"mensaje": "", "recomendado": ""})
        self.assertEqual(self.recargar().subestado, "por_asignar")
        self.assertEqual(set(mail.outbox[0].to), {"ana@correo.com", "luis@correo.com"})

    def test_no_aceptar_con_mensaje_y_recomendacion(self):
        solicitud = self.enviar(self.rosa)
        mail.outbox.clear()
        self.client.force_login(self.rosa)
        self.client.post(reverse("proyectos:no_aceptar_solicitud", args=[solicitud.pk]),
                         {"mensaje": "Este semestre no puedo", "recomendado": self.pablo.pk})
        correo = mail.outbox[0]
        self.assertIn("Este semestre no puedo", correo.body)
        self.assertIn("Pablo Ríos", correo.body)
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse("proyectos:elegir_revisor", args=[self.proyecto.slug]))
        self.assertContains(respuesta, "Recomendado por Rosa Vera")
        self.assertEqual(respuesta.context["recomendacion"]["profesor"], self.pablo)

    def test_no_se_recomienda_a_un_autor(self):
        solicitud = self.enviar(self.rosa)
        with self.assertRaises(ValidationError):
            solicitudes.no_aceptar(solicitud, self.rosa, recomendado=self.rosa)


class RetirarTests(BaseSolicitudes):
    def test_antes_de_5_dias_no_y_despues_si(self):
        solicitud = self.enviar(self.rosa)
        url = reverse("proyectos:retirar_solicitud", args=[self.proyecto.slug])
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(url).status_code, 403)
        SolicitudRevision.objects.filter(pk=solicitud.pk).update(creada_en=timezone.now() - timedelta(days=5, minutes=1))
        mail.outbox.clear()
        self.assertContains(self.client.get(self.proyecto.get_absolute_url()), "Retirar la solicitud")
        self.assertRedirects(self.client.post(url), reverse("proyectos:elegir_revisor", args=[self.proyecto.slug]))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, EstadoSolicitud.RETIRADA)
        self.assertEqual(mail.outbox[0].to, ["rosa@correo.com"])
        self.assertEqual(self.recargar().subestado, "por_asignar")

    def test_un_coautor_no_retira(self):
        solicitud = self.enviar(self.rosa)
        SolicitudRevision.objects.filter(pk=solicitud.pk).update(creada_en=timezone.now() - timedelta(days=6))
        self.client.force_login(self.luis)
        self.assertEqual(self.client.post(reverse("proyectos:retirar_solicitud", args=[self.proyecto.slug])).status_code, 403)


class ReenvioYPermisosTests(BaseSolicitudes):
    def test_reenvio_con_observaciones_vuelve_al_mismo_profesor(self):
        solicitudes.aceptar(self.enviar(self.rosa), self.rosa)
        cambiar_estado(self.proyecto, Estado.CON_OBSERVACIONES, self.rosa, "Agrega pruebas")
        self.client.force_login(self.ana)
        self.assertNotContains(self.client.get(reverse("proyectos:enviar", args=[self.proyecto.slug])), "Elige quién revisa")
        self.client.post(reverse("proyectos:enviar", args=[self.proyecto.slug]), {"comentario": "Listo"})
        proyecto = self.recargar()
        self.assertEqual((proyecto.estado, proyecto.subestado, proyecto.revisor), (Estado.ENVIADO, "por_revisar", self.rosa))
        self.client.force_login(self.rosa)
        self.assertContains(self.client.get(reverse("proyectos:bandeja")), proyecto.titulo)
        self.client.post(reverse("proyectos:tomar", args=[proyecto.slug]))
        self.assertEqual(self.recargar().estado, Estado.EN_REVISION)

    def test_solo_el_revisor_asignado_decide(self):
        solicitudes.aceptar(self.enviar(self.rosa), self.rosa)
        for usuario in (self.pablo, self.admin):
            with self.assertRaises(PermissionDenied):
                cambiar_estado(self.proyecto, Estado.APROBADO, usuario)
        cambiar_estado(self.proyecto, Estado.APROBADO, self.rosa)
        self.assertEqual(self.recargar().revisor, self.rosa)


class ReasignarTests(BaseSolicitudes):
    def test_el_admin_reasigna_y_queda_en_el_historial(self):
        solicitud = self.enviar(self.rosa)
        url = reverse("proyectos:reasignar", args=[self.proyecto.slug])
        self.client.force_login(self.rosa)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        mail.outbox.clear()
        respuesta = self.client.post(url, {"profesor": self.pablo.pk, "motivo": "Rosa está de licencia"})
        self.assertRedirects(respuesta, reverse("proyectos:bandeja"))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, EstadoSolicitud.REASIGNADA)
        proyecto = self.recargar()
        self.assertEqual((proyecto.revisor, proyecto.subestado), (self.pablo, "por_revisar"))
        evento = proyecto.eventos.get(accion=AccionEvento.REASIGNADA)
        self.assertEqual((evento.actor, evento.profesor, evento.comentario), (self.admin, self.pablo, "Rosa está de licencia"))
        self.assertEqual(mail.outbox[0].to, ["pablo@correo.com"])

    def test_reasignar_en_revision_sigue_en_revision(self):
        solicitudes.aceptar(self.enviar(self.rosa), self.rosa)
        solicitudes.reasignar(self.proyecto, self.pablo, self.admin)
        proyecto = self.recargar()
        self.assertEqual((proyecto.estado, proyecto.revisor), (Estado.EN_REVISION, self.pablo))


class DisponibilidadTests(BaseSolicitudes):
    def test_desactivar_no_afecta_lo_asignado(self):
        solicitudes.aceptar(self.enviar(self.rosa), self.rosa)
        self.client.force_login(self.rosa)
        self.client.post(reverse("cuentas:disponibilidad"), {"recibiendo": "0", "next": reverse("vitrina:panel")})
        self.rosa.perfil.refresh_from_db()
        self.assertFalse(self.rosa.perfil.recibiendo_proyectos)
        self.assertEqual(self.recargar().revisor, self.rosa)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(reverse("cuentas:disponibilidad"), {"recibiendo": "0"}).status_code, 403)


class SugerenciasTests(BaseSolicitudes):
    def aprobado_por(self, profesor, asignatura, titulo):
        return crear_proyecto(self.luis, titulo=titulo, estado=Estado.APROBADO, revisor=profesor, asignatura=asignatura)

    def test_puntaje_y_motivos(self):
        otra_del_semestre = Asignatura.objects.filter(semestre=self.asignatura.semestre).exclude(pk=self.asignatura.pk).first()
        self.rosa.perfil.asignaturas_imparte.add(self.asignatura)  # +3
        for i in range(5):  # +2 por cada uno, con tope de 3 → +6
            self.aprobado_por(self.pablo, self.asignatura, f"Aprobado {i}")
        self.aprobado_por(self.rosa, otra_del_semestre, "Del semestre")  # +1
        django = Tecnologia.objects.get(nombre="Django")
        self.proyecto.tecnologias.set([django])
        self.rosa.perfil.aptitudes.add(Aptitud.objects.create(nombre="django"))  # +1
        sugerencias = solicitudes.sugerir_profesores(self.proyecto)
        puntajes = {s["profesor"].email: s["puntaje"] for s in sugerencias}
        self.assertEqual(puntajes, {"pablo@correo.com": 6, "rosa@correo.com": 5})
        motivos_rosa = next(s["motivos"] for s in sugerencias if s["profesor"] == self.rosa)
        self.assertIn(f"Imparte {self.asignatura.nombre}", motivos_rosa)
        self.assertIn("Ha revisado proyectos del mismo semestre", motivos_rosa)
        self.assertIn("Conoce Django", motivos_rosa)
        motivos_pablo = next(s["motivos"] for s in sugerencias if s["profesor"] == self.pablo)
        self.assertIn("Ha revisado 5 proyectos de esta asignatura", motivos_pablo)

    def test_desempate_por_menos_pendientes_y_limite(self):
        for profe in (self.rosa, self.pablo):
            profe.perfil.asignaturas_imparte.add(self.asignatura)
        otro = crear_proyecto(self.luis, titulo="Pendiente de Rosa")
        cambiar_estado(otro, Estado.ENVIADO, self.luis)
        SolicitudRevision.objects.create(proyecto=otro, profesor=self.rosa)
        sugerencias = solicitudes.sugerir_profesores(self.proyecto)
        self.assertEqual([s["profesor"] for s in sugerencias], [self.pablo, self.rosa])
        self.assertEqual(len(solicitudes.sugerir_profesores(self.proyecto, limite=1)), 1)

    def test_sin_puntos_no_se_sugiere(self):
        self.assertEqual(solicitudes.sugerir_profesores(self.proyecto), [])


class HistorialTests(BaseSolicitudes):
    def test_todo_queda_en_el_historial(self):
        solicitud = self.enviar(self.rosa)
        solicitudes.no_aceptar(solicitud, self.rosa, "No puedo", self.pablo)
        segunda = solicitudes.solicitar(self.proyecto, self.pablo, self.ana)
        SolicitudRevision.objects.filter(pk=segunda.pk).update(creada_en=timezone.now() - timedelta(days=6))
        segunda.refresh_from_db()
        solicitudes.retirar(segunda, self.ana)
        acciones = list(self.proyecto.eventos.values_list("accion", flat=True))
        self.assertEqual(acciones, ["estado", "solicitud", "no_aceptada", "solicitud", "retirada"])
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.proyecto.get_absolute_url())
        self.assertContains(respuesta, "pidió la revisión a Rosa Vera")
        self.assertContains(respuesta, "recomendó a Pablo Ríos")


class RecordatorioTests(BaseSolicitudes):
    def test_recordatorio_al_tercer_dia(self):
        from django.core.management import call_command

        solicitud = self.enviar(self.rosa)
        mail.outbox.clear()
        call_command("recordar_solicitudes", verbosity=0)
        self.assertEqual(len(mail.outbox), 0)  # todavía no pasaron 3 días
        SolicitudRevision.objects.filter(pk=solicitud.pk).update(creada_en=timezone.now() - timedelta(days=3, minutes=1))
        call_command("recordar_solicitudes", verbosity=0)
        call_command("recordar_solicitudes", verbosity=0)  # no se repite
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Recordatorio", mail.outbox[0].subject)


class MigracionSolicitudesTests(TransactionTestCase):
    """0016: los proyectos en revisión reciben una solicitud aceptada a nombre de su revisor."""

    serialized_rollback = True

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def otras(self):
        return [n for n in MigrationExecutor(connection).loader.graph.leaf_nodes() if n[0] != "proyectos"]

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_datos(self):
        apps = self.migrar([("proyectos", "0015_solicitudes_revision"), *self.otras()])
        Usuario = apps.get_model("cuentas", "Usuario")
        Proyecto = apps.get_model("proyectos", "Proyecto")
        profe = Usuario.objects.create(email="mig-profe@correo.com", nombres="P", apellidos="Q")
        datos = {"resumen": "r", "descripcion": "d", "repositorio": "https://github.com/uteq/x",
                 "asignatura": apps.get_model("proyectos", "Asignatura").objects.first()}
        en_revision = Proyecto.objects.create(titulo="A", slug="mig-sol-a", estado="en_revision", revisor=profe, **datos)
        enviado = Proyecto.objects.create(titulo="B", slug="mig-sol-b", estado="enviado", **datos)

        apps = self.migrar([("proyectos", "0016_solicitudes_existentes"), *self.otras()])
        Solicitud = apps.get_model("proyectos", "SolicitudRevision")
        self.assertEqual(list(Solicitud.objects.filter(proyecto_id=en_revision.pk).values_list("profesor_id", "estado")),
                         [(profe.pk, "aceptada")])
        self.assertFalse(Solicitud.objects.filter(proyecto_id=enviado.pk).exists())  # queda "Por asignar"
        Solicitud.objects.filter(proyecto_id=en_revision.pk).delete()
        apps.get_model("proyectos", "Proyecto").objects.filter(slug__startswith="mig-sol-").delete()
        apps.get_model("cuentas", "Usuario").objects.filter(email="mig-profe@correo.com").delete()


