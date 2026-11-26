"""Rutas de proyectos: las de los estudiantes y las de la revisión docente."""

from django.urls import path

from proyectos import views

app_name = "proyectos"

urlpatterns = [
    path("mis-proyectos/", views.mis_proyectos, name="mis_proyectos"),
    # Periodos académicos (admins, spec 008)
    path("periodos/", views.periodos, name="periodos"),
    path("periodos/nuevo/", views.periodo_formulario, name="periodo_nuevo"),
    path("periodos/<int:pk>/editar/", views.periodo_formulario, name="periodo_editar"),
    path("periodos/<int:pk>/marcar-actual/", views.periodo_marcar_actual, name="periodo_marcar_actual"),
    path("periodos/<int:pk>/eliminar/", views.periodo_eliminar, name="periodo_eliminar"),
    # Plan de estudios (admins, spec 009)
    path("planes/", views.planes, name="planes"),
    path("planes/nuevo/", views.plan_formulario, name="plan_nuevo"),
    path("planes/<int:pk>/", views.plan, name="plan"),
    path("planes/<int:pk>/editar/", views.plan_formulario, name="plan_editar"),
    path("planes/<int:pk>/activar/", views.plan_activar, name="plan_activar"),
    path("planes/<int:pk>/eliminar/", views.plan_eliminar, name="plan_eliminar"),
    path("planes/<int:plan_pk>/asignaturas/nueva/", views.asignatura_formulario, name="asignatura_nueva"),
    path("asignaturas/<int:pk>/editar/", views.asignatura_formulario, name="asignatura_editar"),
    path("asignaturas/<int:pk>/activar/", views.asignatura_activar, name="asignatura_activar"),
    path("asignaturas/<int:pk>/eliminar/", views.asignatura_eliminar, name="asignatura_eliminar"),
    path("nuevo/", views.crear, name="crear"),
    path("<slug:slug>/editar/", views.editar, name="editar"),
    path("<slug:slug>/eliminar/", views.eliminar, name="eliminar"),
    path("<slug:slug>/enviar/", views.enviar, name="enviar"),
    # Revisor elegido por el creador (spec 009)
    path("<slug:slug>/elegir-revisor/", views.elegir_revisor, name="elegir_revisor"),
    path("<slug:slug>/retirar-solicitud/", views.retirar_solicitud, name="retirar_solicitud"),
    path("<slug:slug>/reasignar/", views.reasignar, name="reasignar"),
    path("<slug:slug>/salir/", views.salir, name="salir"),
    path("<slug:slug>/transferir/", views.transferir, name="transferir"),
    # Revisión (profesores y admins)
    path("revision/", views.bandeja, name="bandeja"),
    path("solicitudes/", views.lista_solicitudes, name="solicitudes"),
    path("solicitudes/<int:pk>/aceptar/", views.aceptar_solicitud, name="aceptar_solicitud"),
    path("solicitudes/<int:pk>/no-aceptar/", views.no_aceptar_solicitud, name="no_aceptar_solicitud"),
    path("<slug:slug>/tomar/", views.tomar, name="tomar"),
    path("<slug:slug>/revisar/", views.revisar, name="revisar"),
]
