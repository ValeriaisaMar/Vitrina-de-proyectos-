"""Recordatorio por correo de las solicitudes de revisión sin responder (spec 009, opcional).

Manda un solo recordatorio a cada profesor cuya solicitud lleva 3 días o más pendiente. Se
programa para que corra una vez al día, por ejemplo con el Programador de tareas de Windows o
con cron en el servidor:

    python manage.py recordar_solicitudes
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from proyectos.correos import avisar_solicitud
from proyectos.solicitudes import recordatorios_pendientes


class Command(BaseCommand):
    help = "Recuerda por correo las solicitudes de revisión que llevan 3 días o más sin respuesta."

    def handle(self, *args, **opciones):
        base = settings.SITIO_URL or "http://localhost:8000"
        enviados = 0
        for solicitud in recordatorios_pendientes():
            if avisar_solicitud(base, solicitud, recordatorio=True):
                solicitud.recordatorio_enviado = True
                solicitud.save(update_fields=["recordatorio_enviado"])
                enviados += 1
        self.stdout.write(f"Recordatorios enviados: {enviados}")
