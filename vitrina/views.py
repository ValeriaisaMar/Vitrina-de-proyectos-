from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def inicio(request):
    return HttpResponse("Vitrina de Proyectos: Ningun proyecto se pierde")