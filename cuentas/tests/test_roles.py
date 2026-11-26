"""Spec 008, historia 1: varios roles por persona, rol activo, selector y reglas de seguridad."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from cuentas.models import CambioRol, Rol, RolAsignado
from cuentas.roles import CLAVE_SESION, asignar_roles
from cuentas.tests.utilidades import CLAVE, crear_usuario
from proyectos.models import Estado, Proyecto
from proyectos.servicios import cambiar_estado, puede_cambiar
from proyectos.tests.utilidades import crear_proyecto, tomar

PANEL = reverse("vitrina:panel")
CAMBIAR = reverse("cuentas:cambiar_rol")
USUARIOS = reverse("cuentas:usuarios")


def editar(usuario):
    return reverse("cuentas:usuario_editar", args=[usuario.pk])


class ModeloTests(TestCase):
    def test_roles_ordenados_y_tiene_rol(self):
        ana = crear_usuario(roles=["admin", "estudiante"])
        self.assertEqual(ana.roles, ["estudiante", "admin"])
        self.assertTrue(ana.tiene_rol(Rol.ADMIN))
        self.assertFalse(ana.tiene_rol(Rol.PROFESOR))

    def test_rol_por_defecto_es_el_ultimo_usado_o_el_de_menor_privilegio(self):
        ana = crear_usuario(roles=["estudiante", "profesor"])
        self.assertEqual(ana.rol_por_defecto(), Rol.ESTUDIANTE)
        ana.ultimo_rol = Rol.PROFESOR
        self.assertEqual(ana.rol_por_defecto(), Rol.PROFESOR)
        ana.ultimo_rol = Rol.ADMIN  # ya no lo tiene: se ignora
        self.assertEqual(ana.rol_por_defecto(), Rol.ESTUDIANTE)

    def test_crear_superusuario_le_da_el_rol_admin(self):
        from django.contrib.auth import get_user_model

        root = get_user_model().objects.create_superuser(email="root@uteq.edu.ec", password=CLAVE, nombres="R", apellidos="T")
        self.assertEqual(root.roles, ["admin"])

    def test_asignar_registra_quien_y_cuando(self):
        admin = crear_usuario("admin@correo.com", rol="admin")
        ana = crear_usuario()
        agregados, quitados = asignar_roles(ana, ["estudiante", "profesor"], admin)
        self.assertEqual((agregados, quitados), (["profesor"], []))
        cambio = CambioRol.objects.get(usuario=ana)
        self.assertEqual((cambio.rol, cambio.accion, cambio.hecho_por), (Rol.PROFESOR, "agregado", admin))
        self.assertEqual(RolAsignado.objects.get(usuario=ana, rol=Rol.PROFESOR).asignado_por, admin)


class SelectorDeRolTests(TestCase):
    def setUp(self):
        self.ana = crear_usuario(roles=["estudiante", "admin"])
        self.client.force_login(self.ana)

    def test_el_encabezado_muestra_el_rol_activo_y_el_selector(self):
        respuesta = self.client.get(PANEL)
        self.assertContains(respuesta, "Cambiar de rol")
        self.assertContains(respuesta, f'action="{CAMBIAR}"', count=1)  # un solo menú, el del avatar (spec 009)
        self.assertContains(respuesta, 'name="rol" value="admin"')
        self.assertTemplateUsed(respuesta, "vitrina/paneles/estudiante.html")  # entra con el de menor privilegio

    def test_con_un_solo_rol_no_hay_selector(self):
        self.client.force_login(crear_usuario("luis@correo.com"))
        respuesta = self.client.get(PANEL)
        self.assertNotContains(respuesta, "Cambiar de rol")
        self.assertContains(respuesta, "insignia-rol")

    def test_cambiar_de_rol_lleva_al_panel_de_ese_rol_y_se_recuerda(self):
        respuesta = self.client.post(CAMBIAR, {"rol": "admin"})
        self.assertRedirects(respuesta, PANEL, fetch_redirect_response=False)
        self.assertEqual(self.client.session[CLAVE_SESION], "admin")
        self.assertTemplateUsed(self.client.get(PANEL), "vitrina/paneles/admin.html")
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.ultimo_rol, "admin")

    def test_al_volver_a_entrar_usa_el_ultimo_rol(self):
        self.client.post(CAMBIAR, {"rol": "admin"})
        self.client.logout()
        self.client.login(username=self.ana.email, password=CLAVE)
        self.assertTemplateUsed(self.client.get(PANEL), "vitrina/paneles/admin.html")

    def test_cambiar_de_rol_solo_por_post(self):
        self.assertEqual(self.client.get(CAMBIAR, {"rol": "admin"}).status_code, 405)

    def test_no_puede_elegir_un_rol_que_no_tiene(self):
        self.client.post(CAMBIAR, {"rol": "profesor"})
        self.assertEqual(self.client.session[CLAVE_SESION], "estudiante")
        self.assertTemplateUsed(self.client.get(PANEL), "vitrina/paneles/estudiante.html")

    def test_los_permisos_dependen_del_rol_activo(self):
        self.assertEqual(self.client.get(USUARIOS).status_code, 403)  # tiene admin, pero actúa como estudiante
        self.client.post(CAMBIAR, {"rol": "admin"})
        self.assertEqual(self.client.get(USUARIOS).status_code, 200)
        self.assertEqual(self.client.get(reverse("proyectos:mis_proyectos")).status_code, 403)

    def test_perfil_muestra_mis_roles(self):
        respuesta = self.client.get(reverse("cuentas:perfil"))
        self.assertContains(respuesta, "Mis roles")
        self.assertContains(respuesta, "Admin")


class SesionManipuladaTests(TestCase):
    def test_un_rol_ajeno_en_la_sesion_se_ignora(self):
        luis = crear_usuario("luis@correo.com")
        self.client.force_login(luis)
        sesion = self.client.session
        sesion[CLAVE_SESION] = "admin"
        sesion.save()
        self.assertTemplateUsed(self.client.get(PANEL), "vitrina/paneles/estudiante.html")
        self.assertEqual(self.client.get(USUARIOS).status_code, 403)
        self.assertEqual(self.client.session[CLAVE_SESION], "estudiante")

    def test_si_le_quitan_el_rol_activo_pasa_al_de_por_defecto(self):
        admin = crear_usuario("admin@correo.com", rol="admin")
        profe = crear_usuario("profe@correo.com", roles=["estudiante", "profesor"])
        self.client.force_login(profe)
        self.client.post(CAMBIAR, {"rol": "profesor"})
        self.assertEqual(self.client.get(reverse("proyectos:bandeja")).status_code, 200)
        asignar_roles(profe, ["estudiante"], admin)
        self.assertEqual(self.client.get(reverse("proyectos:bandeja")).status_code, 403)
        self.assertTemplateUsed(self.client.get(PANEL), "vitrina/paneles/estudiante.html")


class GestionDeRolesTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin@correo.com", rol="admin", nombres="Ada")
        self.ana = crear_usuario()
        self.client.force_login(self.admin)

    def test_dar_y_quitar_roles_con_casillas(self):
        respuesta = self.client.post(editar(self.ana), {"roles": ["estudiante", "profesor"], "is_active": "on"})
        self.assertRedirects(respuesta, USUARIOS, fetch_redirect_response=False)
        self.ana.olvidar_roles()
        self.assertEqual(self.ana.roles, ["estudiante", "profesor"])
        self.client.post(editar(self.ana), {"roles": ["profesor"], "is_active": "on"})
        self.ana.olvidar_roles()
        self.assertEqual(self.ana.roles, ["profesor"])
        self.assertEqual(CambioRol.objects.filter(usuario=self.ana).count(), 2)

    def test_toda_cuenta_conserva_al_menos_un_rol(self):
        respuesta = self.client.post(editar(self.ana), {"is_active": "on"})
        self.assertContains(respuesta, "al menos un rol")
        self.assertEqual(self.ana.roles, ["estudiante"])

    def test_la_lista_muestra_etiquetas_y_filtra_por_rol(self):
        asignar_roles(self.ana, ["estudiante", "profesor"], self.admin)
        respuesta = self.client.get(USUARIOS, {"rol": "profesor"})
        self.assertEqual([u.email for u in respuesta.context["pagina"].object_list], [self.ana.email])
        self.assertContains(respuesta, '<span class="insignia-rol ">Profesor</span>', html=False)
        estudiantes = self.client.get(USUARIOS, {"rol": "estudiante"}).context["pagina"].object_list
        self.assertEqual([u.email for u in estudiantes], [self.ana.email])  # tiene los dos roles, sale una vez

    def test_no_se_quita_el_rol_admin_al_ultimo_admin(self):
        respuesta = self.client.post(editar(self.admin), {"roles": ["estudiante"], "confirmar_quitar_admin": "on"})
        self.assertContains(respuesta, "única cuenta admin activa")
        self.admin.olvidar_roles()
        self.assertTrue(self.admin.tiene_rol(Rol.ADMIN))

    def test_quitarse_el_rol_admin_pide_confirmacion(self):
        crear_usuario("otra@correo.com", rol="admin")
        respuesta = self.client.post(editar(self.admin), {"roles": ["estudiante"]})
        self.assertContains(respuesta, "Confirma que quieres quitarte el rol admin")
        self.admin.olvidar_roles()
        self.assertTrue(self.admin.tiene_rol(Rol.ADMIN))

        respuesta = self.client.post(editar(self.admin), {"roles": ["estudiante"], "confirmar_quitar_admin": "on"})
        self.assertRedirects(respuesta, PANEL, fetch_redirect_response=False)
        self.admin.olvidar_roles()
        self.assertEqual(self.admin.roles, ["estudiante"])
        self.assertEqual(self.client.get(USUARIOS).status_code, 403)  # en su siguiente petición ya no es admin

    def test_nadie_se_desactiva_a_si_mismo(self):
        crear_usuario("otra@correo.com", rol="admin")
        self.client.post(editar(self.admin), {"roles": ["admin"]})  # sin is_active: el campo está bloqueado
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)


class ConflictoDeInteresTests(TestCase):
    def setUp(self):
        self.profe = crear_usuario("profe@correo.com", roles=["estudiante", "profesor"])
        self.otro = crear_usuario("otro@correo.com", rol="profesor")
        self.proyecto = crear_proyecto(self.profe, titulo="Proyecto del profe")
        cambiar_estado(self.proyecto, Estado.ENVIADO, self.profe)  # actúa como estudiante (rol por defecto)

    def test_su_proyecto_no_aparece_en_su_bandeja(self):
        self.client.force_login(self.profe)
        self.client.post(CAMBIAR, {"rol": "profesor"})
        self.assertNotContains(self.client.get(reverse("proyectos:bandeja")), "Proyecto del profe")
        Proyecto.objects.filter(pk=self.proyecto.pk).update(revisor=self.otro)  # se lo asignan a otro (spec 009)
        self.client.force_login(self.otro)
        self.assertContains(self.client.get(reverse("proyectos:bandeja")), "Proyecto del profe")

    def test_no_puede_tomar_ni_decidir_su_proyecto(self):
        self.profe.rol_activo = Rol.PROFESOR
        self.assertFalse(puede_cambiar(self.profe, self.proyecto, Estado.EN_REVISION))
        self.client.force_login(self.profe)
        self.client.post(CAMBIAR, {"rol": "profesor"})
        self.assertEqual(self.client.post(reverse("proyectos:tomar", args=[self.proyecto.slug])).status_code, 403)
        respuesta = self.client.get(reverse("proyectos:revisar", args=[self.proyecto.slug]))
        self.assertContains(respuesta, "Eres autor de este proyecto")

    def test_un_admin_autor_tampoco_lo_decide(self):
        jefa = crear_usuario("jefa@correo.com", roles=["estudiante", "admin"])
        proyecto = crear_proyecto(jefa, titulo="De la jefa")
        cambiar_estado(proyecto, Estado.ENVIADO, jefa)
        tomar(proyecto, self.otro)
        jefa.rol_activo = Rol.ADMIN
        self.assertFalse(puede_cambiar(jefa, proyecto, Estado.APROBADO))


class MigracionDeRolesTests(TransactionTestCase):
    """La migración 0003 copia el rol único de cada usuario a RolAsignado, y se puede revertir."""

    serialized_rollback = True
    antes = [("cuentas", "0002_roles_asignados")]
    despues = [("cuentas", "0004_quitar_rol_unico")]

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def tearDown(self):
        self.migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_copia_cada_rol_y_al_revertir_lo_restaura(self):
        apps = self.migrar(self.antes)
        Usuario = apps.get_model("cuentas", "Usuario")
        profe = Usuario.objects.create(email="profe@x.com", nombres="P", apellidos="R", rol="profesor")
        alumna = Usuario.objects.create(email="alumna@x.com", nombres="A", apellidos="L", rol="estudiante")

        apps = self.migrar(self.despues)
        RolAsignado = apps.get_model("cuentas", "RolAsignado")
        Usuario = apps.get_model("cuentas", "Usuario")
        self.assertEqual(list(RolAsignado.objects.filter(usuario_id=profe.pk).values_list("rol", flat=True)), ["profesor"])
        self.assertEqual(list(RolAsignado.objects.filter(usuario_id=alumna.pk).values_list("rol", flat=True)), ["estudiante"])
        self.assertEqual(Usuario.objects.get(pk=profe.pk).ultimo_rol, "profesor")
        RolAsignado.objects.create(usuario_id=alumna.pk, rol="admin")  # ahora tiene dos

        apps = self.migrar([("cuentas", "0001_initial")])
        Usuario = apps.get_model("cuentas", "Usuario")
        self.assertEqual(Usuario.objects.get(pk=profe.pk).rol, "profesor")
        self.assertEqual(Usuario.objects.get(pk=alumna.pk).rol, "admin")  # el de mayor privilegio
        Usuario.objects.all().delete()
