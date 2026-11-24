"""Rutas de los estudiantes para sus proyectos."""

from django.urls import path

from proyectos import views

app_name = "proyectos"

urlpatterns = [
    path("mis-proyectos/", views.mis_proyectos, name="mis_proyectos"),
    path("nuevo/", views.crear, name="crear"),
    path("<slug:slug>/editar/", views.editar, name="editar"),
    path("<slug:slug>/eliminar/", views.eliminar, name="eliminar"),
]
