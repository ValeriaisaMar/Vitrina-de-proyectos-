"""Rutas de proyectos: las de los estudiantes y las de la revisión docente."""

from django.urls import path

from proyectos import views

app_name = "proyectos"

urlpatterns = [
    path("mis-proyectos/", views.mis_proyectos, name="mis_proyectos"),
    # Periodos académicos (admins, spec 008)
    path("periodos/", views.periodos, name="periodos"),
    path("periodos/nuevo/", views.periodo_formulario, name="periodo_nuevo"),
    path("periodos/<int:pk>/editar/", views.periodo_formulario, name="periodo_editar"),
    path("periodos/<int:pk>/abrir-cerrar/", views.periodo_abrir_cerrar, name="periodo_abrir_cerrar"),
    path("periodos/<int:pk>/eliminar/", views.periodo_eliminar, name="periodo_eliminar"),
    path("nuevo/", views.crear, name="crear"),
    path("<slug:slug>/editar/", views.editar, name="editar"),
    path("<slug:slug>/eliminar/", views.eliminar, name="eliminar"),
    path("<slug:slug>/enviar/", views.enviar, name="enviar"),
    path("<slug:slug>/salir/", views.salir, name="salir"),
    path("<slug:slug>/transferir/", views.transferir, name="transferir"),
    # Revisión (profesores y admins)
    path("revision/", views.bandeja, name="bandeja"),
    path("<slug:slug>/tomar/", views.tomar, name="tomar"),
    path("<slug:slug>/revisar/", views.revisar, name="revisar"),
]
