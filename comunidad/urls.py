"""Rutas de comunidad."""

from django.urls import path
from django.views.generic import RedirectView

from comunidad import views

app_name = "comunidad"

urlpatterns = [
    path("guardados/", views.guardados, name="guardados"),
    # Spec 009: "Favoritos" pasó a llamarse "Guardados"; la dirección vieja redirige (301)
    path("favoritos/", RedirectView.as_view(pattern_name="comunidad:guardados", permanent=True), name="favoritos"),
    path("proyecto/<slug:slug>/me-gusta/", views.me_gusta, name="me_gusta"),
    path("proyecto/<slug:slug>/guardar/", views.guardar, name="guardar"),
    path("proyecto/<slug:slug>/favorito/", views.guardar),  # dirección vieja (formularios en caché)
    path("proyecto/<slug:slug>/comentar/", views.comentar, name="comentar"),
    path("comentario/<int:pk>/ocultar/", views.ocultar, name="ocultar"),
    path("comentario/<int:pk>/borrar/", views.borrar, name="borrar"),
    path("comentario/<int:pk>/responder/", views.responder, name="responder"),
]
