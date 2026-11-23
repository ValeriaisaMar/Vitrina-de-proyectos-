from django.urls import path
from . import views

urlpatterns = [path("", views.inicio, name="inicio"), 
               path("registro/", views.Registro.as_view(), name="registro")]