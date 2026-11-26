"""Formulario de comentarios."""

from django import forms
from django.utils.translation import gettext_lazy as _

from comunidad.models import MAX_COMENTARIO, Comentario
from config.texto import FormularioNFC


class FormularioComentario(FormularioNFC, forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ("texto",)
        labels = {"texto": _("Tu comentario")}
        widgets = {"texto": forms.Textarea(attrs={"rows": 3, "maxlength": MAX_COMENTARIO})}

    def clean_texto(self):
        texto = self.cleaned_data["texto"].strip()
        if len(texto) < 2:
            raise forms.ValidationError(_("Escribe al menos 2 caracteres."))
        return texto
