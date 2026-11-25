"""Pruebas del modelo Proyecto, los datos iniciales y los validadores."""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Asignatura, Estado, Proyecto, Tecnologia
from proyectos.tests.utilidades import crear_proyecto, pdf
from proyectos.validadores import validar_imagen, validar_pdf, validar_url_web


class DatosInicialesTests(TestCase):
    def test_la_malla_de_software_esta_cargada(self):
        self.assertEqual(Asignatura.objects.count(), 53)
        self.assertEqual(set(Asignatura.objects.values_list("semestre", flat=True)), set(range(1, 11)))
        self.assertTrue(Asignatura.objects.filter(nombre="Programación orientada a objetos").exists())

    def test_hay_tecnologias_iniciales(self):
        self.assertTrue(Tecnologia.objects.filter(nombre="Django").exists())
        self.assertGreaterEqual(Tecnologia.objects.count(), 40)


class ProyectoTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")

    def test_el_slug_se_genera_y_no_se_repite(self):
        uno = crear_proyecto(self.ana, titulo="Gestor de Tutorías")
        dos = crear_proyecto(self.ana, titulo="Gestor de tutorías")
        self.assertEqual(uno.slug, "gestor-de-tutorias")
        self.assertEqual(dos.slug, "gestor-de-tutorias-2")

    def test_creador_y_autores(self):
        luis = crear_usuario("luis@correo.com")
        proyecto = crear_proyecto(self.ana, coautores=[luis])
        self.assertEqual(proyecto.creador, self.ana)
        self.assertTrue(proyecto.es_autor(luis))
        self.assertFalse(proyecto.es_autor(crear_usuario("otro@correo.com")))

    def test_solo_los_aprobados_son_publicos(self):
        crear_proyecto(self.ana, titulo="Borrador")
        aprobado = crear_proyecto(self.ana, titulo="Listo", estado=Estado.APROBADO)
        self.assertEqual(list(Proyecto.objects.publicados()), [aprobado])
        self.assertTrue(aprobado.publicado)

    def test_estados_editables(self):
        proyecto = crear_proyecto(self.ana)
        for estado, editable in [(Estado.BORRADOR, True), (Estado.CON_OBSERVACIONES, True),
                                 (Estado.ENVIADO, False), (Estado.EN_REVISION, False),
                                 (Estado.APROBADO, False), (Estado.RECHAZADO, False)]:
            proyecto.estado = estado
            self.assertEqual(proyecto.editable, editable, estado)

    def test_la_asignatura_no_se_puede_borrar_si_tiene_proyectos(self):
        from django.db.models import ProtectedError

        proyecto = crear_proyecto(self.ana)
        with self.assertRaises(ProtectedError):
            proyecto.asignatura.delete()


class ValidadoresTests(TestCase):
    def test_pdf_real(self):
        validar_pdf(pdf())

    def test_pdf_falso_con_extension_correcta(self):
        with self.assertRaises(ValidationError):
            validar_pdf(SimpleUploadedFile("trampa.pdf", b"MZ esto es un ejecutable"))

    def test_pdf_con_otra_extension(self):
        with self.assertRaises(ValidationError):
            validar_pdf(pdf(nombre="informe.docx"))

    def test_pdf_demasiado_grande(self):
        grande = pdf(contenido=b"%PDF-" + b"0" * (10 * 1024 * 1024))
        with self.assertRaises(ValidationError):
            validar_pdf(grande)

    def test_imagen_extension_y_tamano(self):
        with self.assertRaises(ValidationError):
            validar_imagen(SimpleUploadedFile("foto.gif", b"GIF89a"))
        with self.assertRaises(ValidationError):
            validar_imagen(SimpleUploadedFile("foto.png", b"0" * (3 * 1024 * 1024 + 1)))

    def test_solo_enlaces_http_y_https(self):
        validar_url_web("https://github.com/uteq/x")
        for malo in ("javascript:alert(1)", "ftp://servidor/archivo", "github.com/uteq"):
            with self.assertRaises(ValidationError, msg=malo):
                validar_url_web(malo)

    def test_el_periodo_ya_no_tiene_formato_fijo(self):
        """Spec 008: el periodo es un modelo con nombre libre; validar_periodo solo queda para la migración 0001."""
        from proyectos.models import Periodo, Proyecto

        self.assertEqual(Proyecto._meta.get_field("periodo").related_model, Periodo)
        self.assertEqual(Proyecto._meta.get_field("periodo").validators, [])
