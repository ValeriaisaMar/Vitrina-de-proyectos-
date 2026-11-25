"""Rutas de comunidad."""

from django.urls import path

from comunidad import views

app_name = "comunidad"

urlpatterns = [
    path("favoritos/", views.mis_favoritos, name="favoritos"),
    path("proyecto/<slug:slug>/me-gusta/", views.me_gusta, name="me_gusta"),
    path("proyecto/<slug:slug>/favorito/", views.favorito, name="favorito"),
    path("proyecto/<slug:slug>/comentar/", views.comentar, name="comentar"),
    path("comentario/<int:pk>/ocultar/", views.ocultar, name="ocultar"),
    path("comentario/<int:pk>/borrar/", views.borrar, name="borrar"),
    path("comentario/<int:pk>/responder/", views.responder, name="responder"),
]
