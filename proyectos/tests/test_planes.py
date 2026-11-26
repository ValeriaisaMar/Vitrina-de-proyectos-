"""Spec 009, historia 3: planes de estudio y asignaturas administrables."""

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.forms import FormularioProyecto
from proyectos.models import Asignatura, PlanEstudio
from proyectos.tests.utilidades import crear_proyecto

PLANES = reverse("proyectos:planes")


class GestionDePlanesTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("admin@correo.com", rol=Rol.ADMIN))
        self.plan = PlanEstudio.objects.create(nombre="Plan 2026", anio=2026)

    def test_solo_el_admin(self):
        urls = [PLANES, reverse("proyectos:plan_nuevo"), reverse("proyectos:plan", args=[self.plan.pk]),
                reverse("proyectos:asignatura_nueva", args=[self.plan.pk])]
        for rol in (Rol.ESTUDIANTE, Rol.PROFESOR):
            self.client.force_login(crear_usuario(f"{rol}@correo.com", rol=rol))
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 403, url)
            self.assertEqual(self.client.post(reverse("proyectos:plan_activar", args=[self.plan.pk])).status_code, 403)

    def test_crear_plan_y_asignatura(self):
        respuesta = self.client.post(reverse("proyectos:plan_nuevo"), {"nombre": "Plan  2030", "anio": 2030, "activo": "on"})
        plan = PlanEstudio.objects.get(nombre="Plan 2030")
        self.assertRedirects(respuesta, reverse("proyectos:plan", args=[plan.pk]))
        self.client.post(reverse("proyectos:asignatura_nueva", args=[plan.pk]),
                         {"nombre": "Bases de datos", "codigo": "ISW-301", "semestre": 3, "activa": "on"})
        asignatura = Asignatura.objects.get(plan=plan)
        self.assertEqual((asignatura.nombre, asignatura.codigo, asignatura.semestre), ("Bases de datos", "ISW-301", 3))
        self.assertContains(self.client.get(reverse("proyectos:plan", args=[plan.pk])), "Bases de datos")

    def test_nombre_unico_dentro_del_plan_pero_no_entre_planes(self):
        Asignatura.objects.create(plan=self.plan, nombre="Bases de datos", semestre=3)
        respuesta = self.client.post(reverse("proyectos:asignatura_nueva", args=[self.plan.pk]),
                                     {"nombre": "bases  de DATOS", "semestre": 3, "activa": "on"})
        self.assertContains(respuesta, "Ya existe una asignatura con ese nombre en este plan")
        otro = PlanEstudio.objects.create(nombre="Plan 2030", anio=2030)
        Asignatura.objects.create(plan=otro, nombre="Bases de datos", semestre=4)  # en otro plan sí
        with self.assertRaises(IntegrityError), transaction.atomic():
            Asignatura.objects.create(plan=self.plan, nombre="Bases de datos", semestre=5)

    def test_no_se_borra_lo_que_esta_en_uso(self):
        usada = Asignatura.objects.create(plan=self.plan, nombre="Usada", semestre=1)
        libre = Asignatura.objects.create(plan=self.plan, nombre="Libre", semestre=1)
        crear_proyecto(crear_usuario("ana@correo.com"), asignatura=usada)
        self.client.post(reverse("proyectos:asignatura_eliminar", args=[usada.pk]))
        self.assertTrue(Asignatura.objects.filter(pk=usada.pk).exists())
        self.client.post(reverse("proyectos:asignatura_eliminar", args=[libre.pk]))
        self.assertFalse(Asignatura.objects.filter(pk=libre.pk).exists())
        respuesta = self.client.post(reverse("proyectos:plan_eliminar", args=[self.plan.pk]), follow=True)
        self.assertContains(respuesta, "Desactívalo")
        self.assertTrue(PlanEstudio.objects.filter(pk=self.plan.pk).exists())
        vacio = PlanEstudio.objects.create(nombre="Vacío", anio=2020)
        self.client.post(reverse("proyectos:plan_eliminar", args=[vacio.pk]))
        self.assertFalse(PlanEstudio.objects.filter(pk=vacio.pk).exists())

    def test_activar_y_desactivar(self):
        asignatura = Asignatura.objects.create(plan=self.plan, nombre="X", semestre=1)
        self.client.post(reverse("proyectos:asignatura_activar", args=[asignatura.pk]))
        self.client.post(reverse("proyectos:plan_activar", args=[self.plan.pk]))
        asignatura.refresh_from_db()
        self.plan.refresh_from_db()
        self.assertFalse(asignatura.activa)
        self.assertFalse(self.plan.activo)

    def test_el_panel_del_admin_enlaza_el_plan_de_estudios(self):
        self.assertContains(self.client.get(reverse("vitrina:panel")), PLANES)


class SelectorDeAsignaturasTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.plan = PlanEstudio.objects.create(nombre="Plan 2030", anio=2030)
        self.activa = Asignatura.objects.create(plan=self.plan, nombre="Activa nueva", semestre=2, codigo="AN-2")
        self.inactiva = Asignatura.objects.create(plan=self.plan, nombre="Inactiva", semestre=2, activa=False)
        inactivo = PlanEstudio.objects.create(nombre="Plan viejo", anio=2000, activo=False)
        self.de_plan_inactivo = Asignatura.objects.create(plan=inactivo, nombre="Del plan viejo", semestre=1)

    def test_solo_ofrece_activas_de_planes_activos_agrupadas(self):
        campo = FormularioProyecto(usuario=self.ana).fields["asignatura"]
        opciones = set(campo.queryset)
        self.assertIn(self.activa, opciones)
        self.assertNotIn(self.inactiva, opciones)
        self.assertNotIn(self.de_plan_inactivo, opciones)
        grupos = dict(campo.widget.choices[1:])
        self.assertIn((self.activa.pk, "Activa nueva (AN-2)"), grupos["Plan 2030 · Semestre II"])
        self.assertIn("data-buscable", str(FormularioProyecto(usuario=self.ana)["asignatura"]))

    def test_el_proyecto_conserva_su_asignatura_desactivada(self):
        proyecto = crear_proyecto(self.ana, asignatura=self.inactiva)
        campo = FormularioProyecto(instance=proyecto, usuario=self.ana).fields["asignatura"]
        self.assertIn(self.inactiva, set(campo.queryset))


class MigracionPlanVigenteTests(TransactionTestCase):
    """0013: todas las asignaturas pasan a "Plan vigente" y las casi repetidas se fusionan."""

    serialized_rollback = True
    antes = [("proyectos", "0012_planes_de_estudio")]
    despues = [("proyectos", "0014_plan_obligatorio")]

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_plan_vigente_y_fusiones(self):
        apps = self.migrar(self.antes)
        Asignatura = apps.get_model("proyectos", "Asignatura")
        Proyecto = apps.get_model("proyectos", "Proyecto")
        original = Asignatura.objects.create(nombre="Mig Bases de datos", semestre=3)
        repetida = Asignatura.objects.create(nombre="mig  bases de DATOS ", semestre=3)
        datos = {"resumen": "r", "descripcion": "d", "repositorio": "https://github.com/uteq/x"}
        proyecto = Proyecto.objects.create(titulo="A", slug="mig-plan", asignatura=repetida, **datos)
        total = Asignatura.objects.count()

        apps = self.migrar(self.despues)
        Asignatura = apps.get_model("proyectos", "Asignatura")
        Proyecto = apps.get_model("proyectos", "Proyecto")
        self.assertEqual(Asignatura.objects.count(), total - 1)
        self.assertFalse(Asignatura.objects.filter(plan__isnull=True).exists())
        self.assertEqual(set(Asignatura.objects.values_list("plan__nombre", flat=True)), {"Plan vigente"})
        self.assertEqual(Proyecto.objects.get(pk=proyecto.pk).asignatura_id, original.pk)  # el proyecto no se pierde
        Proyecto.objects.filter(pk=proyecto.pk).delete()
        Asignatura.objects.filter(pk=original.pk).delete()
