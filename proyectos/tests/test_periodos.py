"""Spec 008, historia 2: el admin administra los periodos académicos."""

import datetime

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.forms import FormularioProyecto
from proyectos.models import Estado, Periodo
from proyectos.tests.utilidades import crear_proyecto, periodo

LISTA = reverse("proyectos:periodos")
NUEVO = reverse("proyectos:periodo_nuevo")


class GestionDePeriodosTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.client.force_login(self.admin)

    def test_solo_el_admin_entra(self):
        for rol in (Rol.ESTUDIANTE, Rol.PROFESOR):
            self.client.force_login(crear_usuario(f"{rol}@correo.com", rol=rol))
            self.assertEqual(self.client.get(LISTA).status_code, 403)
            self.assertEqual(self.client.post(NUEVO, {}).status_code, 403)

    def test_crear_un_periodo_con_nombre_libre(self):
        respuesta = self.client.post(NUEVO, {
            "nombre": "Intensivo  noviembre 2026", "tipo": "intensivo",
            "fecha_inicio": "2026-11-02", "fecha_fin": "2026-11-28",
        })
        self.assertRedirects(respuesta, LISTA, fetch_redirect_response=False)
        creado = Periodo.objects.get(nombre="Intensivo noviembre 2026")
        self.assertEqual((creado.slug, creado.tipo, creado.es_actual), ("intensivo-noviembre-2026", "intensivo", False))

    def test_el_nombre_es_unico_y_las_fechas_coherentes(self):
        periodo("2026-2")
        respuesta = self.client.post(NUEVO, {"nombre": "2026-2", "tipo": "ordinario", "fecha_inicio": "2026-07-01"})
        self.assertContains(respuesta, "Ya existe un periodo con ese nombre")
        respuesta = self.client.post(NUEVO, {"nombre": "Raro", "tipo": "otro", "fecha_inicio": "2026-07-01", "fecha_fin": "2026-06-01"})
        self.assertContains(respuesta, "no puede ser anterior")

    def test_editar_cambia_el_slug(self):
        p = periodo("Verano")
        self.client.post(reverse("proyectos:periodo_editar", args=[p.pk]),
                         {"nombre": "Verano 2027", "tipo": "intersemestral", "fecha_inicio": "2027-01-10"})
        p.refresh_from_db()
        self.assertEqual((p.nombre, p.slug), ("Verano 2027", "verano-2027"))


    def test_la_lista_muestra_el_numero_de_proyectos(self):
        crear_proyecto(crear_usuario("ana@correo.com"), periodo="2025-1")
        respuesta = self.client.get(LISTA)
        self.assertContains(respuesta, "2025-1")
        self.assertEqual(respuesta.context["periodos"].get(nombre="2025-1").total_proyectos, 1)

    def test_no_se_borra_un_periodo_con_proyectos(self):
        crear_proyecto(crear_usuario("ana@correo.com"), periodo="2025-1")
        con_proyectos = Periodo.objects.get(nombre="2025-1")
        self.client.post(reverse("proyectos:periodo_eliminar", args=[con_proyectos.pk]))
        self.assertTrue(Periodo.objects.filter(pk=con_proyectos.pk).exists())
        vacio = periodo("Sin uso")
        self.client.post(reverse("proyectos:periodo_eliminar", args=[vacio.pk]))
        self.assertFalse(Periodo.objects.filter(pk=vacio.pk).exists())

    def test_el_panel_del_admin_enlaza_los_periodos(self):
        self.assertContains(self.client.get(reverse("vitrina:panel")), LISTA)


class PeriodoEnElFormularioTests(TestCase):
    def test_el_formulario_ya_no_pide_periodo(self):
        """Spec 009: el período se asigna al enviar, no se elige."""
        self.assertNotIn("periodo", FormularioProyecto(usuario=crear_usuario("ana@correo.com")).fields)


class PeriodoEnLaVitrinaTests(TestCase):
    def setUp(self):
        ana = crear_usuario("ana@correo.com")
        self.intensivo = periodo("Intensivo noviembre 2026", fecha_inicio=datetime.date(2026, 11, 2), tipo="intensivo")
        crear_proyecto(ana, titulo="Del intensivo", estado=Estado.APROBADO, periodo=self.intensivo)
        crear_proyecto(ana, titulo="Del 2025", estado=Estado.APROBADO, periodo="2025-1")
        crear_proyecto(ana, titulo="Borrador", periodo=periodo("2024-1"))

    def test_filtro_con_slug_legible_y_del_mas_reciente_al_mas_antiguo(self):
        respuesta = self.client.get(reverse("vitrina:explorar"), {"periodo": "intensivo-noviembre-2026"})
        titulos = [p.titulo for p in respuesta.context["pagina"].object_list]
        self.assertEqual(titulos, ["Del intensivo"])
        self.assertContains(respuesta, "Intensivo noviembre 2026")  # chip con el nombre
        opciones = list(respuesta.context["form"].fields["periodo"].queryset.values_list("nombre", flat=True))
        self.assertEqual(opciones, ["Intensivo noviembre 2026", "2025-1"])  # el del borrador no aparece

    def test_el_panel_del_admin_cuenta_aprobados_por_periodo(self):
        self.client.force_login(crear_usuario("admin@correo.com", rol=Rol.ADMIN))
        filas = self.client.get(reverse("vitrina:panel")).context["periodos"]
        self.assertEqual([f["etiqueta"] for f in filas], ["Intensivo noviembre 2026", "2025-1"])


class MigracionDePeriodosTests(TransactionTestCase):
    """La migración 0006 crea un Periodo por cada texto distinto y se puede revertir."""

    serialized_rollback = True
    antes = [("proyectos", "0005_periodo")]
    despues = [("proyectos", "0007_periodo_como_relacion")]

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_crea_periodos_y_asigna_cada_proyecto(self):
        apps = self.migrar(self.antes)
        Proyecto = apps.get_model("proyectos", "Proyecto")
        asignatura = apps.get_model("proyectos", "Asignatura").objects.first()
        datos = {"resumen": "r", "descripcion": "d", "asignatura": asignatura, "repositorio": "https://github.com/uteq/x"}
        a = Proyecto.objects.create(titulo="A", slug="a", periodo="2025-2", **datos)
        b = Proyecto.objects.create(titulo="B", slug="b", periodo="2025-2", **datos)
        c = Proyecto.objects.create(titulo="C", slug="c", periodo="2026-1", **datos)

        apps = self.migrar(self.despues)
        Proyecto = apps.get_model("proyectos", "Proyecto")
        Periodo = apps.get_model("proyectos", "Periodo")
        p2025 = Periodo.objects.get(nombre="2025-2")
        self.assertEqual((p2025.tipo, p2025.fecha_inicio, p2025.slug), ("ordinario", datetime.date(2025, 7, 1), "2025-2"))
        self.assertEqual(Periodo.objects.get(nombre="2026-1").fecha_inicio, datetime.date(2026, 1, 1))
        self.assertEqual(Proyecto.objects.get(pk=a.pk).periodo_id, p2025.pk)
        self.assertEqual(Proyecto.objects.get(pk=b.pk).periodo_id, p2025.pk)
        self.assertEqual(Proyecto.objects.get(pk=c.pk).periodo.nombre, "2026-1")

        apps = self.migrar(self.antes)  # vuelta: el texto se recupera
        Proyecto = apps.get_model("proyectos", "Proyecto")
        self.assertEqual(Proyecto.objects.get(pk=a.pk).periodo, "2025-2")
        Proyecto.objects.all().delete()
