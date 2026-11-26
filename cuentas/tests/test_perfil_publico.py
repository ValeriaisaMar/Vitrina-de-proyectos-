"""Spec 009, historia 4: perfil público de cada usuario."""

import io

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from PIL import Image

from cuentas.models import Aptitud, Rol
from cuentas.perfiles import (
    digito_verificador_orcid,
    normalizar_github,
    normalizar_linkedin,
    normalizar_orcid,
    personas_relacionadas,
)
from cuentas.roles import asignar_roles
from cuentas.tests.utilidades import crear_usuario
from proyectos.models import Estado
from proyectos.tests.utilidades import MediaTemporal, crear_proyecto


class CreacionDelPerfilTests(TestCase):
    def test_toda_cuenta_nueva_tiene_perfil_con_slug_legible(self):
        ana = crear_usuario("ana@correo.com", nombres="Ana", apellidos="Pérez")
        self.assertEqual(ana.perfil.slug, "ana-perez")
        otra = crear_usuario("otra@correo.com", nombres="Ana", apellidos="Pérez")
        self.assertEqual(otra.perfil.slug, "ana-perez-2")

    def test_el_slug_no_cambia_si_cambia_el_nombre(self):
        ana = crear_usuario("ana@correo.com", nombres="Ana", apellidos="Pérez")
        ana.nombres = "Anabel"
        ana.save()
        ana.perfil.refresh_from_db()
        self.assertEqual(ana.perfil.slug, "ana-perez")


class VisibilidadTests(TestCase):
    def url(self, usuario):
        return reverse("vitrina:persona", args=[usuario.perfil.slug])

    def test_estudiante_visible_para_visitantes(self):
        ana = crear_usuario("ana@correo.com")
        respuesta = self.client.get(self.url(ana))
        self.assertContains(respuesta, "Ana Pérez")
        self.assertContains(respuesta, "Estudiante")
        self.assertNotContains(respuesta, "ana@correo.com")  # el correo nunca se muestra

    def test_profesor_aunque_tambien_sea_estudiante(self):
        luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora", rol=Rol.PROFESOR)
        asignar_roles(luis, [Rol.ESTUDIANTE, Rol.PROFESOR], None)
        self.assertContains(self.client.get(self.url(luis)), "Profesor")

    def test_solo_admin_o_inactivo_es_404(self):
        admin = crear_usuario("admin@correo.com", rol=Rol.ADMIN)
        self.assertEqual(self.client.get(self.url(admin)).status_code, 404)
        inactiva = crear_usuario("inactiva@correo.com", activo=False)
        self.assertEqual(self.client.get(self.url(inactiva)).status_code, 404)

    def test_bloques_vacios_no_se_muestran(self):
        ana = crear_usuario("ana@correo.com")
        respuesta = self.client.get(self.url(ana))
        for titulo in ("Aptitudes", "Experiencia laboral", "Estudios", "Proyectos publicados", "Personas relacionadas"):
            self.assertNotContains(respuesta, titulo)
        perfil = ana.perfil
        perfil.descripcion = "Me gusta programar."
        perfil.save()
        perfil.aptitudes.add(Aptitud.objects.create(nombre="Django"))
        respuesta = self.client.get(self.url(ana))
        self.assertContains(respuesta, "Me gusta programar.")
        self.assertContains(respuesta, "Aptitudes")
        self.assertNotContains(respuesta, "Estudios")


class ValidacionDeEnlacesTests(TestCase):
    def test_github(self):
        self.assertEqual(normalizar_github("octocat"), "https://github.com/octocat")
        self.assertEqual(normalizar_github("https://www.github.com/octocat/"), "https://github.com/octocat")
        for malo in ("https://github.com/a/b", "mal_nombre!", "https://gitlab.com/x"):
            with self.assertRaises(ValidationError):
                normalizar_github(malo)

    def test_linkedin(self):
        self.assertEqual(normalizar_linkedin("linkedin.com/in/ana-paz"), "https://www.linkedin.com/in/ana-paz")
        self.assertEqual(normalizar_linkedin("https://www.linkedin.com/in/ana-paz/"), "https://www.linkedin.com/in/ana-paz")
        for malo in ("https://www.linkedin.com/company/uteq", "ana-paz", "https://example.com/in/ana"):
            with self.assertRaises(ValidationError):
                normalizar_linkedin(malo)

    def test_orcid_con_digito_verificador(self):
        self.assertEqual(normalizar_orcid("0000-0002-1825-0097"), "0000-0002-1825-0097")
        self.assertEqual(normalizar_orcid("https://orcid.org/0000000218250097"), "0000-0002-1825-0097")
        with self.assertRaises(ValidationError):
            normalizar_orcid("0000-0002-1825-0098")  # dígito de control equivocado
        with self.assertRaises(ValidationError):
            normalizar_orcid("1234-5678")
        # Un ORCID cuyo dígito de control es X
        base = next(f"{n:015d}" for n in range(1000) if digito_verificador_orcid(f"{n:015d}") == "X")
        con_x = f"{base}x"
        self.assertTrue(normalizar_orcid(con_x).endswith("X"))


class EdicionTests(MediaTemporal, TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.url = reverse("vitrina:persona", args=[self.ana.perfil.slug])
        self.client.force_login(self.ana)

    def test_el_dueno_ve_editar_perfil_y_los_demas_no(self):
        self.assertContains(self.client.get(self.url), "Editar perfil")
        self.client.force_login(crear_usuario("luis@correo.com"))
        self.assertNotContains(self.client.get(self.url), "Editar perfil")
        self.assertEqual(self.client.post(self.url, {"seccion": "descripcion", "descripcion-descripcion": "x"}).status_code, 403)

    def test_descripcion_y_enlaces(self):
        self.client.post(self.url, {"seccion": "descripcion", "descripcion-descripcion": "Hola"})
        self.client.post(self.url, {"seccion": "enlaces", "enlaces-github": "octocat", "enlaces-linkedin": "", "enlaces-orcid": ""})
        self.ana.perfil.refresh_from_db()
        self.assertEqual((self.ana.perfil.descripcion, self.ana.perfil.github), ("Hola", "https://github.com/octocat"))

    def test_un_enlace_invalido_muestra_el_error_sin_perder_lo_escrito(self):
        respuesta = self.client.post(self.url, {"seccion": "enlaces", "enlaces-github": "", "enlaces-linkedin": "", "enlaces-orcid": "0000-0002-1825-0098"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "dígito de control")
        self.assertContains(respuesta, "0000-0002-1825-0098")

    def test_aptitudes_se_reutilizan_sin_distinguir_mayusculas(self):
        Aptitud.objects.create(nombre="Django")
        self.client.post(self.url, {"seccion": "aptitudes", "aptitudes-aptitudes": "django, Flutter, flutter"})
        self.assertEqual(sorted(self.ana.perfil.aptitudes.values_list("nombre", flat=True)), ["Django", "Flutter"])
        self.assertEqual(Aptitud.objects.filter(nombre__iexact="django").count(), 1)

    def test_agregar_y_quitar_experiencia_y_estudios(self):
        self.client.post(self.url, {"seccion": "experiencia", "experiencia-cargo": "Desarrolladora", "experiencia-organizacion": "UTEQ",
                                    "experiencia-inicio": "2024-03", "experiencia-actualmente": "on"})
        self.client.post(self.url, {"seccion": "estudio", "estudio-institucion": "UTEQ", "estudio-titulo": "Ingeniería de Software",
                                    "estudio-inicio": "2022-04", "estudio-fin": "2021-01"})  # fin antes del inicio: no se guarda
        experiencia = self.ana.perfil.experiencias.get()
        self.assertIsNone(experiencia.fin)
        self.assertFalse(self.ana.perfil.estudios.exists())
        self.assertContains(self.client.get(self.url), "Actualmente")
        otra = crear_usuario("luis@correo.com").perfil
        ajena = otra.experiencias.create(cargo="X", organizacion="Y", inicio="2020-01-01")
        self.client.post(self.url, {"seccion": "quitar_experiencia", "pk": ajena.pk})  # no es suya: no se borra
        self.assertTrue(otra.experiencias.filter(pk=ajena.pk).exists())
        self.client.post(self.url, {"seccion": "quitar_experiencia", "pk": experiencia.pk})
        self.assertFalse(self.ana.perfil.experiencias.exists())

    def test_foto_se_guarda_como_webp_con_nombre_aleatorio(self):
        buffer = io.BytesIO()
        Image.new("RGB", (900, 500), (2, 90, 39)).save(buffer, "JPEG")
        self.client.post(self.url, {"seccion": "foto", "foto": SimpleUploadedFile("mi-cara.jpg", buffer.getvalue())})
        self.ana.perfil.refresh_from_db()
        nombre = self.ana.perfil.foto.name
        self.assertTrue(nombre.startswith("perfiles/fotos/") and nombre.endswith(".webp"))
        self.assertNotIn("mi-cara", nombre)
        with Image.open(self.ana.perfil.foto.path) as foto:
            self.assertEqual(foto.size, (400, 400))

    def test_foto_falsa_se_rechaza(self):
        respuesta = self.client.post(self.url, {"seccion": "foto", "foto": SimpleUploadedFile("cara.jpg", b"no es imagen")})
        self.assertContains(respuesta, "no es una imagen válida")


class PersonasRelacionadasTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com", nombres="Ana", apellidos="Paz")
        self.luis = crear_usuario("luis@correo.com", nombres="Luis", apellidos="Mora")
        self.profe = crear_usuario("profe@correo.com", nombres="Rosa", apellidos="Vera", rol=Rol.PROFESOR)

    def relacionados(self, usuario):
        return {t["perfil"].usuario.email: t["en_comun"] for t in personas_relacionadas(usuario)}

    def test_solo_proyectos_aprobados_sin_duplicados(self):
        crear_proyecto(self.ana, titulo="Uno", estado=Estado.APROBADO, coautores=[self.luis], revisor=self.profe)
        crear_proyecto(self.ana, titulo="Dos", estado=Estado.APROBADO, coautores=[self.luis], revisor=self.profe)
        crear_proyecto(self.ana, titulo="Borrador", coautores=[crear_usuario("x@correo.com")])
        self.assertEqual(self.relacionados(self.ana), {"luis@correo.com": 2, "profe@correo.com": 2})
        self.assertEqual(self.relacionados(self.profe), {"ana@correo.com": 2, "luis@correo.com": 2})

    def test_consultas_fijas(self):
        crear_proyecto(self.ana, titulo="Uno", estado=Estado.APROBADO, coautores=[self.luis], revisor=self.profe)
        self.ana.olvidar_roles()
        with CaptureQueriesContext(connection) as antes:
            [t["perfil"].usuario.url_perfil for t in personas_relacionadas(self.ana)]
        for i in range(4):
            otro = crear_usuario(f"c{i}@correo.com", nombres=f"Coautor{i}")
            crear_proyecto(self.ana, titulo=f"P{i}", estado=Estado.APROBADO, coautores=[otro], revisor=self.profe)
        self.ana.olvidar_roles()
        with CaptureQueriesContext(connection) as despues:
            [t["perfil"].usuario.url_perfil for t in personas_relacionadas(self.ana)]
        self.assertEqual(len(despues), len(antes))


class BienvenidaTests(TestCase):
    def test_mas_tarde_no_vuelve_a_salir(self):
        ana = crear_usuario("ana@correo.com")
        self.client.force_login(ana)
        panel = reverse("vitrina:panel")
        self.assertContains(self.client.get(panel), "Completa tu perfil")
        self.assertRedirects(self.client.post(reverse("cuentas:bienvenida"), {"accion": "despues"}), panel)
        respuesta = self.client.get(panel)
        self.assertNotContains(respuesta, "Completa tu perfil")
        self.assertContains(respuesta, "Ver o editar mi perfil público")  # enlace discreto

    def test_completar_ahora_lleva_a_editar(self):
        ana = crear_usuario("ana@correo.com")
        self.client.force_login(ana)
        respuesta = self.client.post(reverse("cuentas:bienvenida"), {"accion": "ahora"})
        self.assertRedirects(respuesta, ana.perfil.get_absolute_url() + "?editar=1")
        ana.perfil.refresh_from_db()
        self.assertTrue(ana.perfil.bienvenida_vista)
