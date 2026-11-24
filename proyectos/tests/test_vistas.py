"""Pruebas de crear, editar, listar y eliminar proyectos, y de quién puede hacerlo."""

from django.test import TestCase
from django.urls import reverse

from cuentas.models import Rol
from cuentas.tests.utilidades import CLAVE, crear_usuario
from proyectos.models import Asignatura, Estado, Proyecto, Tecnologia
from proyectos.tests.utilidades import MediaTemporal, crear_proyecto, imagen_png, pdf


class BaseProyectos(MediaTemporal, TestCase):
    def setUp(self):
        self.ana = crear_usuario("ana@correo.com")
        self.asignatura = Asignatura.objects.get(nombre="Programación orientada a objetos")
        self.django = Tecnologia.objects.get(nombre="Django")

    def entrar(self, usuario):
        self.client.login(username=usuario.email, password=CLAVE)

    def datos(self, **cambios):
        datos = {
            "titulo": "Vitrina de prueba",
            "resumen": "Resumen corto del proyecto.",
            "descripcion": "Descripción completa.",
            "asignatura": self.asignatura.pk,
            "periodo": "2026-2",
            "tecnologias": [self.django.pk],
            "repositorio": "https://github.com/uteq/vitrina",
            "demo": "",
            "coautores": "",
        }
        datos.update(cambios)
        return datos


class CrearTests(BaseProyectos):
    def test_el_visitante_va_al_login(self):
        respuesta = self.client.get(reverse("proyectos:crear"))
        self.assertRedirects(respuesta, reverse("cuentas:entrar") + "?next=" + reverse("proyectos:crear"))

    def test_un_profesor_no_puede_crear(self):
        self.entrar(crear_usuario("profe@correo.com", rol=Rol.PROFESOR))
        self.assertEqual(self.client.get(reverse("proyectos:crear")).status_code, 403)

    def test_crea_un_borrador_con_el_estudiante_como_creador(self):
        self.entrar(self.ana)
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos())
        proyecto = Proyecto.objects.get()
        self.assertRedirects(respuesta, proyecto.get_absolute_url())
        self.assertEqual(proyecto.estado, Estado.BORRADOR)
        self.assertEqual(proyecto.creador, self.ana)
        self.assertEqual(list(proyecto.tecnologias.all()), [self.django])

    def test_coautores_validos(self):
        luis = crear_usuario("luis@correo.com")
        self.entrar(self.ana)
        self.client.post(reverse("proyectos:crear"), self.datos(coautores="LUIS@correo.com, ana@correo.com"))
        proyecto = Proyecto.objects.get()
        self.assertEqual(set(proyecto.autores.all()), {self.ana, luis})

    def test_coautores_sin_cuenta_o_que_no_son_estudiantes(self):
        crear_usuario("profe@correo.com", rol=Rol.PROFESOR)
        crear_usuario("inactivo@correo.com", activo=False)
        self.entrar(self.ana)
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos(
            coautores="nadie@correo.com\nprofe@correo.com\ninactivo@correo.com\nno-es-correo"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Proyecto.objects.exists())
        errores = " ".join(respuesta.context["form"].errors["coautores"])
        self.assertIn("nadie@correo.com", errores)
        self.assertIn("profe@correo.com", errores)
        self.assertIn("inactivo@correo.com", errores)
        self.assertIn("no-es-correo", errores)

    def test_maximo_de_autores(self):
        correos = [crear_usuario(f"e{i}@correo.com").email for i in range(6)]
        self.entrar(self.ana)
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos(coautores=",".join(correos)))
        self.assertFalse(Proyecto.objects.exists())
        self.assertIn("coautores", respuesta.context["form"].errors)

    def test_enlace_con_esquema_peligroso(self):
        self.entrar(self.ana)
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos(repositorio="javascript:alert(1)"))
        self.assertIn("repositorio", respuesta.context["form"].errors)

    def test_maximo_de_tecnologias(self):
        ids = list(Tecnologia.objects.values_list("pk", flat=True)[:9])
        self.entrar(self.ana)
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos(tecnologias=ids))
        self.assertIn("tecnologias", respuesta.context["form"].errors)

    def test_sube_pdf_e_imagenes(self):
        self.entrar(self.ana)
        datos = self.datos(documento_pdf=pdf(), imagenes=[imagen_png("a.png"), imagen_png("b.png")])
        self.client.post(reverse("proyectos:crear"), datos)
        proyecto = Proyecto.objects.get()
        self.assertTrue(proyecto.documento_pdf.name.endswith(".pdf"))
        self.assertEqual(proyecto.imagenes.count(), 2)
        self.assertEqual(proyecto.portada.orden, 1)

    def test_rechaza_un_pdf_falso(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.entrar(self.ana)
        falso = SimpleUploadedFile("informe.pdf", b"no soy un pdf", content_type="application/pdf")
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos(documento_pdf=falso))
        self.assertIn("documento_pdf", respuesta.context["form"].errors)

    def test_rechaza_mas_de_cuatro_imagenes(self):
        self.entrar(self.ana)
        imagenes = [imagen_png(f"{i}.png") for i in range(5)]
        respuesta = self.client.post(reverse("proyectos:crear"), self.datos(imagenes=imagenes))
        self.assertIn("imagenes", respuesta.context["form"].errors)
        self.assertFalse(Proyecto.objects.exists())


class EditarTests(BaseProyectos):
    def setUp(self):
        super().setUp()
        self.luis = crear_usuario("luis@correo.com")
        self.proyecto = crear_proyecto(self.ana, coautores=[self.luis])
        self.url = reverse("proyectos:editar", args=[self.proyecto.slug])

    def test_un_coautor_puede_editar(self):
        self.entrar(self.luis)
        respuesta = self.client.post(self.url, self.datos(titulo="Nuevo título", coautores="luis@correo.com"))
        self.assertRedirects(respuesta, self.proyecto.get_absolute_url())
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.titulo, "Nuevo título")
        self.assertEqual(self.proyecto.creador, self.ana)

    def test_quitar_un_coautor(self):
        self.entrar(self.ana)
        self.client.post(self.url, self.datos(coautores=""))
        self.assertEqual(list(self.proyecto.autores.all()), [self.ana])

    def test_quien_no_es_autor_recibe_403(self):
        self.entrar(crear_usuario("otra@correo.com"))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_no_se_edita_un_proyecto_enviado(self):
        self.proyecto.estado = Estado.ENVIADO
        self.proyecto.save()
        self.entrar(self.ana)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_se_edita_con_observaciones(self):
        self.proyecto.estado = Estado.CON_OBSERVACIONES
        self.proyecto.save()
        self.entrar(self.ana)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_quitar_una_imagen(self):
        self.entrar(self.ana)
        self.client.post(self.url, self.datos(imagenes=[imagen_png("a.png"), imagen_png("b.png")]))
        primera = self.proyecto.imagenes.first()
        self.client.post(self.url, self.datos(quitar_imagenes=[primera.pk]))
        self.assertEqual(self.proyecto.imagenes.count(), 1)


class MisProyectosYEliminarTests(BaseProyectos):
    def test_lista_solo_los_proyectos_propios(self):
        crear_proyecto(self.ana, titulo="El mío")
        crear_proyecto(crear_usuario("otra@correo.com"), titulo="El de otra")
        self.entrar(self.ana)
        respuesta = self.client.get(reverse("proyectos:mis_proyectos"))
        self.assertContains(respuesta, "El mío")
        self.assertNotContains(respuesta, "El de otra")

    def test_el_creador_elimina_un_borrador(self):
        proyecto = crear_proyecto(self.ana)
        self.entrar(self.ana)
        url = reverse("proyectos:eliminar", args=[proyecto.slug])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertRedirects(self.client.post(url), reverse("proyectos:mis_proyectos"))
        self.assertFalse(Proyecto.objects.exists())

    def test_un_coautor_no_puede_eliminar(self):
        luis = crear_usuario("luis@correo.com")
        proyecto = crear_proyecto(self.ana, coautores=[luis])
        self.entrar(luis)
        self.assertEqual(self.client.post(reverse("proyectos:eliminar", args=[proyecto.slug])).status_code, 403)
        self.assertTrue(Proyecto.objects.exists())

    def test_no_se_elimina_despues_de_enviar(self):
        proyecto = crear_proyecto(self.ana, estado=Estado.ENVIADO)
        self.entrar(self.ana)
        self.assertEqual(self.client.post(reverse("proyectos:eliminar", args=[proyecto.slug])).status_code, 403)
