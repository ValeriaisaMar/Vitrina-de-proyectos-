from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView



def inicio(request):
    return render(request, "vitrina/inicio.html", {
        "proyectos": [], "carreras": [], "q": "",
        "carrera_activa": "", "total_verificados": 0, "total_carreras": 0,
    })

class Registro(CreateView):
    form_class = UserCreationForm
    template_name = "registration/registro.html"
    success_url = reverse_lazy("login")