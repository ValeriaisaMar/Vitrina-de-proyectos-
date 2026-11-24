"""Filtros de plantilla para dibujar campos de formulario con el estilo de la Vitrina."""

from django import template

register = template.Library()


@register.filter
def control(campo):
    """Dibuja el control de un campo con la clase del tema y los atributos de accesibilidad.

    Uso en plantillas:  {% load formularios %} … {{ form.email|control }}

    - Agrega la clase "campo-control" (o la de casilla si es un checkbox).
    - Si hay errores, marca aria-invalid y enlaza el mensaje de error con aria-describedby,
      junto con el texto de ayuda si existe, para que un lector de pantalla lea ambos.
    """
    es_casilla = getattr(campo.field.widget, "input_type", "") == "checkbox"
    atributos = {"class": "h-5 w-5 accent-uteq-verde" if es_casilla else "campo-control"}

    descripciones = []
    if campo.help_text:
        descripciones.append(f"{campo.auto_id}_helptext")
    if campo.errors:
        atributos["aria-invalid"] = "true"
        descripciones.append(f"{campo.auto_id}_error")
    if descripciones:
        atributos["aria-describedby"] = " ".join(descripciones)

    return campo.as_widget(attrs=atributos)
