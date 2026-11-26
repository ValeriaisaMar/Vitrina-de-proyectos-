"""Paleta de colores para la portada de un proyecto sin imagen (spec 009, historia 7).

Se guarda la CLAVE ("verde", "azul"…), no el código hexadecimal: si mañana se ajusta un tono, todos
los proyectos que lo usan cambian juntos. La portada lleva texto blanco encima en modo claro y en
modo oscuro, así que cada color tiene contraste de al menos 4.5:1 con el blanco (lo comprueba una
prueba con la fórmula de las pautas WCAG).
"""

from django.utils.translation import gettext_lazy as _

PALETA = {
    "verde": (_("Verde institucional"), "#025a27"),
    "petroleo": (_("Petróleo"), "#0f5f59"),
    "azul": (_("Azul"), "#1e40af"),
    "indigo": (_("Índigo"), "#3730a3"),
    "morado": (_("Morado"), "#6b21a8"),
    "ciruela": (_("Ciruela"), "#86198f"),
    "vino": (_("Vino"), "#9d174d"),
    "terracota": (_("Terracota"), "#9a3412"),
    "ocre": (_("Ocre"), "#7a4a00"),
    "grafito": (_("Grafito"), "#374151"),
}
COLOR_POR_DEFECTO = "verde"
OPCIONES_COLOR = [(clave, nombre) for clave, (nombre, _hex) in PALETA.items()]


def hex_de(clave):
    """El código del color de la clave (o el verde si la clave ya no existe)."""
    return PALETA.get(clave, PALETA[COLOR_POR_DEFECTO])[1]


def contraste_con_blanco(hexadecimal):
    """Razón de contraste WCAG entre el color y el blanco (1 a 21)."""
    def canal(valor):
        valor = valor / 255
        return valor / 12.92 if valor <= 0.03928 else ((valor + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hexadecimal[i:i + 2], 16) for i in (1, 3, 5))
    luminancia = 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)
    return 1.05 / (luminancia + 0.05)
