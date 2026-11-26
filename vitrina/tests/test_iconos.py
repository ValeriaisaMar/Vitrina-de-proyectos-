"""Pruebas de la etiqueta {% icono %} y del filtro |inicial (spec 009)."""

from django.template import Context, Template
from django.test import SimpleTestCase


def pintar(texto, **contexto):
    return Template(texto).render(Context(contexto))


class IconoTests(SimpleTestCase):
    def test_decorativo_por_defecto(self):
        html = pintar('{% icono "bookmark" %}')
        self.assertIn("<svg", html)
        self.assertIn('aria-hidden="true"', html)
        self.assertIn('width="20"', html)

    def test_tamano_clase_y_etiqueta(self):
        html = pintar('{% icono "x" tam=16 clase="shrink-0" etiqueta="Cerrar" %}')
        self.assertIn('width="16" height="16"', html)
        self.assertIn('class="shrink-0"', html)
        self.assertIn('role="img" aria-label="Cerrar"', html)
        self.assertNotIn("aria-hidden", html)

    def test_la_etiqueta_se_escapa(self):
        html = pintar('{% icono "x" etiqueta=valor %}', valor='"><script>')
        self.assertNotIn("<script>", html)

    def test_icono_inexistente_o_nombre_raro_no_rompe(self):
        self.assertEqual(pintar('{% icono "no-existe" %}'), "")
        self.assertEqual(pintar('{% icono "../secreto" %}'), "")

    def test_logos_de_marca(self):
        for nombre in ("marca-github", "marca-linkedin", "marca-orcid"):
            self.assertIn('fill="currentColor"', pintar('{% icono nombre %}', nombre=nombre))


class InicialTests(SimpleTestCase):
    def test_letra_con_tilde_compuesta_o_descompuesta(self):
        self.assertEqual(pintar("{{ t|inicial }}", t="árbol"), "Á")
        self.assertEqual(pintar("{{ t|inicial }}", t="n\u0303andú"), "Ñ")  # NFD: n + tilde

    def test_salta_signos_iniciales(self):
        self.assertEqual(pintar("{{ t|inicial }}", t="¿Sí? ¡Claro!"), "S")
        self.assertEqual(pintar("{{ t|inicial }}", t="«más»"), "M")

    def test_vacio(self):
        self.assertEqual(pintar("{{ t|inicial }}", t=""), "")
