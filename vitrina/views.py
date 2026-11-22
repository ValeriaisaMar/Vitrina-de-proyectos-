from django.shortcuts import render
from django.http import HttpResponse



def inicio(request):
    return render(request, "vitrina/inicio.html", {
        "proyectos": [], "carreras": [], "q": "",
        "carrera_activa": "", "total_verificados": 0, "total_carreras": 0,
    })