"""Spec 009, historia 2c: al renombrar Favorito a Guardado nadie pierde lo que guardó."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MigracionGuardadosTests(TransactionTestCase):
    serialized_rollback = True
    def otras(self):
        """Las demás apps en su última migración: así el estado histórico de Usuario es el actual."""
        hojas = MigrationExecutor(connection).loader.graph.leaf_nodes()
        return [nodo for nodo in hojas if nodo[0] in ("cuentas", "proyectos")]

    @property
    def antes(self):
        return [("comunidad", "0003_texto_nfc"), *self.otras()]

    @property
    def despues(self):
        return [("comunidad", "0004_favorito_a_guardado"), *self.otras()]

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_conserva_los_guardados(self):
        apps = self.migrar(self.antes)
        Usuario = apps.get_model("cuentas", "Usuario")
        Proyecto = apps.get_model("proyectos", "Proyecto")
        Favorito = apps.get_model("comunidad", "Favorito")
        ana = Usuario.objects.create(email="mig-ana@correo.com", nombres="Ana", apellidos="Paz")
        datos = {"resumen": "r", "descripcion": "d", "repositorio": "https://github.com/uteq/x",
                 "asignatura": apps.get_model("proyectos", "Asignatura").objects.first()}
        proyecto = Proyecto.objects.create(titulo="A", slug="mig-guardado", estado="aprobado", **datos)
        Favorito.objects.create(usuario=ana, proyecto=proyecto)

        apps = self.migrar(self.despues)
        Guardado = apps.get_model("comunidad", "Guardado")
        self.assertTrue(Guardado.objects.filter(usuario_id=ana.pk, proyecto_id=proyecto.pk).exists())

        apps = self.migrar(self.antes)  # y de vuelta
        self.assertEqual(apps.get_model("comunidad", "Favorito").objects.count(), 1)
        apps.get_model("comunidad", "Favorito").objects.all().delete()
        apps.get_model("proyectos", "Proyecto").objects.filter(slug="mig-guardado").delete()
        apps.get_model("cuentas", "Usuario").objects.filter(email="mig-ana@correo.com").delete()
