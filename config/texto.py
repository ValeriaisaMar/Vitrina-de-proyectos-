"""Texto con tildes, ñ y signos tipográficos sin "cajitas" (spec 009, historia 2b).

Una misma letra se puede guardar de dos formas en Unicode:
- NFC (compuesta): «ñ» es un solo carácter, U+00F1.
- NFD (descompuesta): «ñ» son dos, «n» + tilde combinante U+0303. Así llega a veces el texto
  copiado de macOS o de un PDF.
El navegador combina las dos sin problema, pero reportlab (el certificado PDF) no compone
caracteres: dibuja la tilde suelta, y si la fuente no tiene un carácter dibuja su glifo vacío,
una caja con una x. Por eso todo texto que escriben las personas se guarda en NFC, y antes de
dibujar en el PDF se reemplazan los caracteres que la fuente no trae.
"""

import unicodedata

# Reemplazos legibles para signos que las fuentes del PDF no traen
_REEMPLAZOS = {
    "→": "->", "←": "<-", "↔": "<->", "⇒": "=>",
    "•": "·", "−": "-", " ": " ", " ": " ", "​": "",
}


def nfc(texto):
    """El texto en forma compuesta (NFC). Devuelve el mismo valor si no es str."""
    if not isinstance(texto, str):
        return texto
    return unicodedata.normalize("NFC", texto)


def para_pdf(texto, tiene_glifo):
    """Prepara un texto para reportlab: NFC y sin caracteres que la fuente no puede dibujar.

    tiene_glifo(caracter) -> bool dice si la fuente trae ese carácter. Si no lo trae se prueba,
    en orden: un reemplazo conocido (→ por ->), su forma de compatibilidad (NFKC: ﬁ → fi) o la
    letra sin tilde (como último recurso); si nada sirve, se omite.
    """
    salida = []
    for caracter in nfc(texto or ""):
        if caracter in "\n\t" or tiene_glifo(caracter):
            salida.append(caracter)
            continue
        candidatos = [
            _REEMPLAZOS.get(caracter),
            unicodedata.normalize("NFKC", caracter),
            "".join(c for c in unicodedata.normalize("NFD", caracter) if not unicodedata.combining(c)),
        ]
        for candidato in candidatos:
            if candidato is not None and candidato != caracter and all(tiene_glifo(c) for c in candidato):
                salida.append(candidato)
                break
    return "".join(salida)


class FormularioNFC:
    """Mezcla para formularios: guarda en NFC todo el texto que escribe la persona.

    Va antes de forms.Form / forms.ModelForm en la herencia. Los ModelForm copian cleaned_data al
    modelo después de clean(), así que basta con normalizar aquí.
    """

    def clean(self):
        datos = super().clean()
        for campo, valor in list(datos.items()):
            if isinstance(valor, str):
                datos[campo] = nfc(valor)
        return datos
