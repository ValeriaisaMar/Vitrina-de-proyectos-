"""Rutas públicas de la vitrina."""

from django.urls import path

from vitrina import paneles, views

app_name = "vitrina"  # permite escribir {% url 'vitrina:inicio' %}

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("explorar/", views.explorar, name="explorar"),
    path("proyecto/<slug:slug>/", views.detalle, name="detalle"),
    path("panel/", paneles.panel, name="panel"),
    path("verificar/", views.verificar, name="verificar"),
    path("verificar/<str:codigo>/", views.verificar_codigo, name="verificar_codigo"),
    path("verificar/<str:codigo>/qr.png", views.descargar_qr, name="qr"),
    path("verificar/<str:codigo>/certificado.pdf", views.descargar_certificado, name="certificado"),
]
