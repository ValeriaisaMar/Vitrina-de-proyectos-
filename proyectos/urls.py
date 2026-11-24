"""Rutas de proyectos: las de los estudiantes y las de la revisión docente."""

from django.urls import path

from proyectos import views

app_name = "proyectos"

urlpatterns = [
    path("mis-proyectos/", views.mis_proyectos, name="mis_proyectos"),
    path("nuevo/", views.crear, name="crear"),
    path("<slug:slug>/editar/", views.editar, name="editar"),
    path("<slug:slug>/eliminar/", views.eliminar, name="eliminar"),
    path("<slug:slug>/enviar/", views.enviar, name="enviar"),
    # Revisión (profesores y admins)
    path("revision/", views.bandeja, name="bandeja"),
    path("<slug:slug>/tomar/", views.tomar, name="tomar"),
    path("<slug:slug>/revisar/", views.revisar, name="revisar"),
]
