"""Ejecutor de pruebas del proyecto (spec 009).

Igual al de Django, con dos agregados:
- Vacía la caché antes de cada prueba. La caché vive en memoria y no se deshace con el rollback
  de cada prueba; sin esto, el "período actual" guardado por una prueba aparecería en la
  siguiente, aunque su fila ya no exista.
- Usa un hasher de contraseñas rápido (MD5) solo durante las pruebas. El de producción es lento
  a propósito (protege contra ataques de fuerza bruta) y hacía que la suite tardara 7 minutos.
  Es la recomendación de la documentación de Django para pruebas; producción no cambia.
- Calla los avisos "Not Found" y "Forbidden" de django.request (spec 010). Desde que los logs salen
  por consola, cada prueba de permisos (que espera un 403 o un 404) imprimía una línea. Los errores
  de verdad (nivel ERROR) se siguen viendo.
"""

import logging
import unittest

from django.conf import settings
from django.core.cache import caches
from django.test.runner import DiscoverRunner


class ResultadoConCacheLimpia(unittest.TextTestResult):
    def startTest(self, test):
        for cache in caches.all():
            cache.clear()
        super().startTest(test)


class Ejecutor(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
        logging.getLogger("django.request").setLevel(logging.ERROR)

    def get_resultclass(self):
        return super().get_resultclass() or ResultadoConCacheLimpia
