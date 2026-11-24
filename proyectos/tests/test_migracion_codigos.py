"""Prueba de la migración 0004: completa los códigos de proyectos aprobados a mano."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CodigosFaltantesTests(TransactionTestCase):
    # Esta clase de prueba vacía la base al terminar; serialized_rollback la deja como estaba
    # (con las asignaturas y tecnologías de la migración 0002) para las pruebas que siguen.
    serialized_rollback = True
    antes = [("proyectos", "0003_eventoestado_consecutivo")]
    despues = [("proyectos", "0004_codigos_faltantes")]

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_asigna_codigos_consecutivos_y_respeta_los_existentes(self):
        apps = self.migrar(self.antes)
        Proyecto = apps.get_model("proyectos", "Proyecto")
        Asignatura = apps.get_model("proyectos", "Asignatura")
        Consecutivo = apps.get_model("proyectos", "Consecutivo")
        asignatura = Asignatura.objects.first()
        datos = {"resumen": "r", "descripcion": "d", "asignatura": asignatura, "periodo": "2026-1",
                 "repositorio": "https://github.com/uteq/x"}
        Consecutivo.objects.create(anio=2026, ultimo=1)
        con_codigo = Proyecto.objects.create(titulo="Ya tenía", slug="ya", estado="aprobado", codigo="VP-2026-0001", **datos)
        sin_codigo = Proyecto.objects.create(titulo="Aprobado a mano", slug="mano", estado="aprobado", **datos)
        borrador = Proyecto.objects.create(titulo="Borrador", slug="borrador", **datos)

        apps = self.migrar(self.despues)
        Proyecto = apps.get_model("proyectos", "Proyecto")
        sin_codigo = Proyecto.objects.get(pk=sin_codigo.pk)
        self.assertRegex(sin_codigo.codigo, r"^VP-\d{4}-\d{4}$")
        self.assertIsNotNone(sin_codigo.aprobado_en)
        self.assertEqual(Proyecto.objects.get(pk=con_codigo.pk).codigo, "VP-2026-0001")
        self.assertIsNone(Proyecto.objects.get(pk=borrador.pk).codigo)
        Proyecto.objects.all().delete()
