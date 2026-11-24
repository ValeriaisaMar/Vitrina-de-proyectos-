"""Rutas públicas de la vitrina."""

from django.urls import path

from vitrina import views

app_name = "vitrina"  # permite escribir {% url 'vitrina:inicio' %}

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("explorar/", views.explorar, name="explorar"),
    path("verificar/", views.verificar, name="verificar"),
]
