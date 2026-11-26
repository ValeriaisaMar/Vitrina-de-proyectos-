"""Spec 009, historia 1: un solo período actual, que se asigna al enviar y al aprobar."""

import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado, Periodo
from proyectos.servicios import cambiar_estado, marcar_actual
from proyectos.tests.utilidades import crear_proyecto, periodo


class UnSoloActualTests(TestCase):
    def test_la_base_de_datos_no_deja_dos_actuales(self):
        periodo("2026-1", actual=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Periodo.objects.create(nombre="2026-2", fecha_inicio=datetime.date(2026, 7, 1), es_actual=True)

    def test_marcar_otro_desmarca_el_anterior(self):
        viejo = periodo("2026-1", actual=True)
        nuevo = periodo("2026-2", actual=False)
        self.assertEqual(marcar_actual(nuevo), viejo)
        self.assertEqual(list(Periodo.objects.filter(es_actual=True)), [nuevo])
        self.assertEqual(Periodo.actual(), nuevo)  # la caché se borró al guardar


class GestionDelActualTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.viejo = periodo("2026-1", actual=True)
        self.nuevo = periodo("2026-2", actual=False)
        self.url = reverse("proyectos:periodo_marcar_actual", args=[self.nuevo.pk])

    def test_pide_confirmacion_y_dice_cual_deja_de_ser_actual(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "dejará de ser el período actual")
        self.assertFalse(Periodo.objects.get(pk=self.nuevo.pk).es_actual)  # GET no cambia nada
        self.assertRedirects(self.client.post(self.url), reverse("proyectos:periodos"))
        self.assertEqual(Periodo.actual(), self.nuevo)

    def test_solo_el_admin(self):
        for rol in (Rol.ESTUDIANTE, Rol.PROFESOR):
            self.client.force_login(crear_usuario(f"{rol}@correo.com", rol=rol))
            self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertFalse(Periodo.objects.get(pk=self.nuevo.pk).es_actual)

    def test_la_lista_marca_el_actual(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("proyectos:periodos"))
        self.assertContains(respuesta, "Período actual")
        self.assertContains(respuesta, self.url)

    def test_no_se_borra_el_actual(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("proyectos:periodo_eliminar", args=[self.viejo.pk]))
        self.assertTrue(Periodo.objects.filter(pk=self.viejo.pk).exists())


class PeriodoAlEnviarYAprobarTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.profe = crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        self.viejo = periodo("2026-1", actual=True)
        self.proyecto = crear_proyecto(self.ana, periodo=None)

    def test_el_proyecto_toma_el_periodo_actual_al_enviar(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.periodo, self.viejo)

    def test_sin_periodo_actual_no_se_puede_enviar(self):
        Periodo.objects.update(es_actual=False)
        with self.assertRaises(ValidationError) as error:
            cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        self.assertEqual(error.exception.code, "sin_periodo")
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.estado, Estado.BORRADOR)

    def test_la_pagina_de_envio_avisa_si_no_hay_periodo(self):
        Periodo.objects.update(es_actual=False)
        Periodo.objects.first().save()  # update() no pasa por save(): se borra la caché a mano
        self.client.force_login(self.ana)
        url = reverse("proyectos:enviar", args=[self.proyecto.slug])
        self.assertContains(self.client.get(url), "No hay un período académico activo. Avísale a la administración.")
        self.client.post(url, {"comentario": ""})
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.estado, Estado.BORRADOR)

    def test_al_aprobar_guarda_el_periodo_de_aprobacion(self):
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.ana)
        marcar_actual(periodo("2026-2", actual=False))  # la revisión cruzó de período
        self.proyecto.refresh_from_db()
        self.proyecto.revisor = self.profe
        self.proyecto.estado = Estado.EN_REVISION
        self.proyecto.save()
        cambiar_estado(self.proyecto, Estado.APROBADO, self.profe)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.periodo.nombre, "2026-1")
        self.assertEqual(self.proyecto.periodo_aprobacion.nombre, "2026-2")

        respuesta = self.client.get(reverse("vitrina:verificar_codigo", args=[self.proyecto.codigo]))
        self.assertContains(respuesta, "Período académico de aprobación")
        self.assertContains(respuesta, "2026-2")


class PeriodoEnElPieTests(TestCase):
    def test_todos_ven_el_periodo_actual(self):
        periodo("2026-2", actual=True)
        self.assertContains(self.client.get(reverse("vitrina:inicio")), "Período académico actual: 2026-2")

    def test_sin_periodo_actual_no_sale_nada(self):
        Periodo.objects.update(es_actual=False)  # las migraciones dejan uno como actual
        self.assertNotContains(self.client.get(reverse("vitrina:inicio")), "Período académico actual")


class MigracionDelPeriodoActualTests(TransactionTestCase):
    """0009: el abierto más reciente queda actual y los aprobados reciben su período de aprobación."""

    serialized_rollback = True
    antes = [("proyectos", "0008_periodo_actual")]
    despues = [("proyectos", "0010_quitar_abierto")]

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_datos(self):
        apps = self.migrar(self.antes)
        Periodo = apps.get_model("proyectos", "Periodo")
        Proyecto = apps.get_model("proyectos", "Proyecto")
        Periodo.objects.update(abierto=False)
        viejo = Periodo.objects.create(nombre="M-2025", slug="m-2025", fecha_inicio=datetime.date(2025, 1, 1), abierto=True)
        reciente = Periodo.objects.create(nombre="M-2026", slug="m-2026", fecha_inicio=datetime.date(2026, 7, 1), abierto=True)
        Periodo.objects.create(nombre="M-2027", slug="m-2027", fecha_inicio=datetime.date(2027, 1, 1), abierto=False)
        asignatura = apps.get_model("proyectos", "Asignatura").objects.first()
        datos = {"resumen": "r", "descripcion": "d", "asignatura": asignatura, "repositorio": "https://github.com/uteq/x"}
        aprobado = Proyecto.objects.create(titulo="A", slug="mig-a", estado="aprobado", periodo=viejo, **datos)
        borrador = Proyecto.objects.create(titulo="B", slug="mig-b", periodo=viejo, **datos)

        apps = self.migrar(self.despues)
        Periodo = apps.get_model("proyectos", "Periodo")
        Proyecto = apps.get_model("proyectos", "Proyecto")
        self.assertEqual(list(Periodo.objects.filter(es_actual=True).values_list("pk", flat=True)), [reciente.pk])
        self.assertEqual(Proyecto.objects.get(pk=aprobado.pk).periodo_aprobacion_id, viejo.pk)
        self.assertIsNone(Proyecto.objects.get(pk=borrador.pk).periodo_aprobacion_id)
        self.assertEqual(Proyecto.objects.get(pk=borrador.pk).periodo_id, viejo.pk)  # nada se pierde
        Proyecto.objects.filter(slug__startswith="mig-").delete()
        Periodo.objects.filter(slug__startswith="m-20").delete()
