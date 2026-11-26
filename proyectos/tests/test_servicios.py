"""Pruebas del servicio de estados: transiciones, permisos, comentarios, historial y código."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado, EventoEstado, HistorialInmutable
from proyectos.servicios import TRANSICIONES, TransicionNoPermitida, cambiar_estado, puede_cambiar
from proyectos.tests.utilidades import crear_proyecto, tomar


class BaseServicio(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        self.otro_profe = crear_usuario("profe2@correo.com", rol=Rol.PROFESOR)
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.proyecto = crear_proyecto(self.ana)

    def llevar_a(self, estado):
        """Recorre el camino normal hasta el estado pedido."""
        camino = {
            Estado.ENVIADO: [(Estado.ENVIADO, self.ana)],
            Estado.EN_REVISION: [(Estado.ENVIADO, self.ana), (Estado.EN_REVISION, self.profe)],
        }
        for nuevo, actor in camino[estado]:
            if nuevo == Estado.EN_REVISION:
                tomar(self.proyecto, actor)  # el profesor asignado empieza la revisión (spec 009)
            else:
                cambiar_estado(self.proyecto, nuevo, actor)


class TransicionesTests(BaseServicio):
    def test_camino_completo_hasta_aprobar(self):
        self.llevar_a(Estado.EN_REVISION)
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe, "Muy buen trabajo")
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.estado, Estado.APROBADO)
        self.assertEqual(self.proyecto.revisor, self.profe)
        self.assertIsNotNone(self.proyecto.aprobado_en)
        estados = list(self.proyecto.eventos.values_list("estado_anterior", "estado_nuevo"))
        self.assertEqual(estados, [("borrador", "enviado"), ("enviado", "en_revision"), ("en_revision", "aprobado")])

    def test_ciclo_de_observaciones(self):
        self.llevar_a(Estado.EN_REVISION)
        cambiar_estado(self.proyecto, Estado.CON_OBSERVACIONES, self.profe, "Falta el manual")
        self.assertTrue(self.proyecto.editable)
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana, "Ya agregué el manual")
        self.assertEqual(self.proyecto.estado, Estado.ENVIADO)
        self.assertEqual(self.proyecto.ultima_decision.comentario, "Falta el manual")

    def test_transiciones_que_no_existen(self):
        prohibidas = [
            (Estado.BORRADOR, Estado.APROBADO, self.admin),
            (Estado.BORRADOR, Estado.EN_REVISION, self.admin),
        ]
        for _desde, hacia, actor in prohibidas:
            with self.assertRaises(TransicionNoPermitida):
                cambiar_estado(self.proyecto, hacia, actor, "x")
        self.assertEqual(self.proyecto.estado, Estado.BORRADOR)
        self.assertFalse(EventoEstado.objects.exists())

    def test_aprobado_y_rechazado_son_finales(self):
        self.llevar_a(Estado.EN_REVISION)
        cambiar_estado(self.proyecto, Estado.RECHAZADO, self.profe, "No cumple el alcance")
        for hacia in Estado.values:
            with self.assertRaises(TransicionNoPermitida, msg=hacia):
                cambiar_estado(self.proyecto, hacia, self.profe, "x")

    def test_la_tabla_es_la_de_la_constitucion(self):
        self.assertEqual(len(TRANSICIONES), 6)


class PermisosTests(BaseServicio):
    def test_solo_un_autor_envia(self):
        for actor in (crear_usuario("otra@correo.com"), self.profe, self.admin):
            with self.assertRaises(PermissionDenied):
                cambiar_estado(self.proyecto, Estado.ENVIADO, actor)
        self.assertTrue(puede_cambiar(self.ana, self.proyecto, Estado.ENVIADO))

    def test_un_coautor_tambien_envia(self):
        luis = crear_usuario("luis@correo.com")
        proyecto = crear_proyecto(self.ana, titulo="Otro", coautores=[luis])
        cambiar_estado(proyecto, Estado.ENVIADO, luis)
        self.assertEqual(proyecto.estado, Estado.ENVIADO)

    def test_un_estudiante_no_toma_proyectos(self):
        self.llevar_a(Estado.ENVIADO)
        with self.assertRaises(PermissionDenied):
            cambiar_estado(self.proyecto, Estado.EN_REVISION, self.ana)

    def test_sin_revisor_asignado_nadie_empieza_la_revision(self):
        """Spec 009: ya no hay bandeja común; ni un profesor cualquiera ni el admin toman proyectos."""
        self.llevar_a(Estado.ENVIADO)
        for actor in (self.profe, self.admin):
            with self.assertRaises(PermissionDenied):
                cambiar_estado(self.proyecto, Estado.EN_REVISION, actor)

    def test_solo_decide_el_profesor_asignado(self):
        """Spec 009: ni otro profesor ni el admin deciden; el admin solo reasigna."""
        self.llevar_a(Estado.EN_REVISION)
        for actor in (self.otro_profe, self.admin):
            with self.assertRaises(PermissionDenied):
                cambiar_estado(self.proyecto, Estado.APROBADO, actor)
            self.assertFalse(puede_cambiar(actor, self.proyecto, Estado.APROBADO))
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe)
        self.assertEqual(self.proyecto.estado, Estado.APROBADO)

    def test_un_segundo_profesor_no_puede_tomar_lo_ya_tomado(self):
        self.llevar_a(Estado.EN_REVISION)
        with self.assertRaises(TransicionNoPermitida):
            cambiar_estado(self.proyecto, Estado.EN_REVISION, self.otro_profe)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.revisor, self.profe)

    def test_lee_el_estado_real_aunque_el_objeto_este_viejo(self):
        self.llevar_a(Estado.ENVIADO)
        copia_vieja = type(self.proyecto).objects.get(pk=self.proyecto.pk)
        tomar(self.proyecto, self.profe)
        with self.assertRaises(TransicionNoPermitida):
            cambiar_estado(copia_vieja, Estado.EN_REVISION, self.otro_profe)


class ComentarioTests(BaseServicio):
    def test_pedir_cambios_y_rechazar_exigen_comentario(self):
        self.llevar_a(Estado.EN_REVISION)
        for hacia in (Estado.CON_OBSERVACIONES, Estado.RECHAZADO):
            with self.assertRaises(ValidationError):
                cambiar_estado(self.proyecto, hacia, self.profe, "   ")
        self.assertEqual(self.proyecto.estado, Estado.EN_REVISION)

    def test_el_evento_guarda_todo(self):
        self.llevar_a(Estado.EN_REVISION)
        evento = cambiar_estado(self.proyecto, Estado.CON_OBSERVACIONES, self.profe, "  Agrega pruebas  ")
        self.assertEqual(
            (evento.estado_anterior, evento.estado_nuevo, evento.actor, evento.comentario),
            (Estado.EN_REVISION, Estado.CON_OBSERVACIONES, self.profe, "Agrega pruebas"),
        )
        self.assertIsNotNone(evento.creado_en)


class HistorialTests(BaseServicio):
    def test_un_evento_no_se_edita_ni_se_borra(self):
        evento = cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana, "Hola")
        evento.comentario = "Cambiado"
        with self.assertRaises(HistorialInmutable):
            evento.save()
        with self.assertRaises(HistorialInmutable):
            evento.delete()
        self.assertEqual(EventoEstado.objects.get().comentario, "Hola")

    def test_no_se_borra_un_proyecto_con_historial(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        with self.assertRaises(ProtectedError):
            self.proyecto.delete()


class CodigoTests(BaseServicio):
    def aprobar(self, proyecto):
        cambiar_estado(proyecto, Estado.ENVIADO, self.ana)
        tomar(proyecto, self.profe)
        cambiar_estado(proyecto, Estado.APROBADO, self.profe)
        return proyecto

    def test_codigos_consecutivos_del_anio(self):
        anio = timezone.localdate().year
        uno = self.aprobar(self.proyecto)
        dos = self.aprobar(crear_proyecto(self.ana, titulo="Segundo"))
        self.assertEqual(uno.codigo, f"VP-{anio}-0001")
        self.assertEqual(dos.codigo, f"VP-{anio}-0002")

    def test_un_proyecto_sin_aprobar_no_tiene_codigo(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        self.proyecto.refresh_from_db()
        self.assertIsNone(self.proyecto.codigo)
