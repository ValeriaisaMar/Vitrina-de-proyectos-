"""Genera el código de la configuración inicial y lo imprime en la terminal (spec 010).

Es el camino principal para crear el primer admin en un servidor nuevo:

    python manage.py codigo_configuracion_inicial
    docker compose exec web python manage.py codigo_configuracion_inicial   (con Docker)

Cada vez que se corre, el código anterior deja de servir. Si ya hay un admin activo, no genera
nada y termina con error.
"""

from django.core.management.base import BaseCommand, CommandError

from cuentas import configuracion_inicial as servicio


class Command(BaseCommand):
    help = "Genera el código de un solo uso para crear el primer admin en /configuracion-inicial/."

    def handle(self, *args, **opciones):
        if servicio.hay_admin_activo():
            raise CommandError("Ya existe un administrador activo. La configuración inicial no está disponible.")
        url = servicio.url_configuracion()
        codigo = servicio.generar_codigo(url, en_el_log=False)
        # Se imprime con self.stdout: sale en la terminal de quien corre el comando, sin depender
        # de cómo esté configurado el log (y sin repetirse dos veces en pantalla).
        self.stdout.write(servicio.bloque(codigo, url))
