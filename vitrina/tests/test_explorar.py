"""Pruebas de la página Explorar: solo aprobados, búsqueda, filtros y paginación."""

from django.test import TestCase
from django.urls import reverse

from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Asignatura, Estado, Tecnologia
from proyectos.tests.utilidades import crear_proyecto

URL = reverse("vitrina:explorar")


class ExplorarTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com", nombres="Ana", apellidos="Zambrano")
        self.tutorias = crear_proyecto(self.ana, titulo="Gestor de tutorías", estado=Estado.APROBADO,
                                       tecnologias=("Django", "PostgreSQL"), periodo="2026-1")
        self.clima = crear_proyecto(crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora"),
                                    titulo="Estación del clima", estado=Estado.APROBADO,
                                    tecnologias=("Arduino",), periodo="2025-2",
                                    resumen="Mide temperatura y humedad en el campus.",
                                    asignatura=Asignatura.objects.get(nombre="Aplicaciones móviles"))
        self.borrador = crear_proyecto(self.ana, titulo="Proyecto secreto", tecnologias=("Django",))

    def titulos(self, **parametros):
        respuesta = self.client.get(URL, parametros)
        self.assertEqual(respuesta.status_code, 200)
        return {p.titulo for p in respuesta.context["pagina"].object_list}

    def test_solo_aparecen_los_aprobados(self):
        self.assertEqual(self.titulos(), {"Gestor de tutorías", "Estación del clima"})

    def test_busca_por_titulo_tecnologia_y_autor(self):
        self.assertEqual(self.titulos(q="tutorías"), {"Gestor de tutorías"})
        self.assertEqual(self.titulos(q="arduino"), {"Estación del clima"})
        self.assertEqual(self.titulos(q="zambrano"), {"Gestor de tutorías"})
        self.assertEqual(self.titulos(q="secreto"), set())

    def test_filtra_por_tecnologia_asignatura_y_periodo(self):
        django = Tecnologia.objects.get(nombre="Django")
        self.assertEqual(self.titulos(tecnologia=django.pk), {"Gestor de tutorías"})
        self.assertEqual(self.titulos(asignatura=self.clima.asignatura_id), {"Estación del clima"})
        self.assertEqual(self.titulos(periodo="2025-2"), {"Estación del clima"})

    def test_las_cuentas_de_tecnologia_ignoran_los_borradores(self):
        respuesta = self.client.get(URL)
        cuentas = {t.nombre: t.total for t in respuesta.context["tecnologias"]}
        self.assertEqual(cuentas["Django"], 1)
        self.assertNotIn("Java", cuentas)

    def test_filtros_activos_y_quitar(self):
        respuesta = self.client.get(URL, {"q": "gestor", "periodo": "2026-1"})
        activos = respuesta.context["filtros_activos"]
        self.assertEqual(len(activos), 2)
        self.assertContains(respuesta, "gestor")
        for filtro in activos:
            self.assertNotIn(filtro["url"].count("="), [0, 3])

    def test_estado_vacio(self):
        respuesta = self.client.get(URL, {"q": "no-existe-nada"})
        self.assertContains(respuesta, "No encontramos proyectos")

    def test_valores_raros_no_rompen_la_pagina(self):
        for parametros in ({"tecnologia": "abc"}, {"asignatura": "999999"}, {"pagina": "9999"},
                           {"orden": "drop table"}, {"periodo": "x"}):
            self.assertEqual(self.client.get(URL, parametros).status_code, 200, parametros)

    def test_paginacion_de_doce(self):
        for i in range(12):
            crear_proyecto(self.ana, titulo=f"Extra {i}", estado=Estado.APROBADO)
        primera = self.client.get(URL)
        self.assertEqual(len(primera.context["pagina"].object_list), 12)
        segunda = self.client.get(URL, {"pagina": 2})
        self.assertEqual(len(segunda.context["pagina"].object_list), 2)

    def test_orden_por_titulo(self):
        respuesta = self.client.get(URL, {"orden": "titulo"})
        titulos = [p.titulo for p in respuesta.context["pagina"].object_list]
        self.assertEqual(titulos, sorted(titulos))
