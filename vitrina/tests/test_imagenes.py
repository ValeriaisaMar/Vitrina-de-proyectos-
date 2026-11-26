"""Pruebas de la validación y conversión de imágenes subidas (config/imagenes.py, spec 009)."""

import io

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from config.imagenes import MB, TAM_FOTO, TAM_PORTADA, convertir_a_webp, validar_imagen_subida


def imagen(nombre="foto.jpg", formato="JPEG", tam=(800, 600)):
    buffer = io.BytesIO()
    Image.new("RGB", tam, (2, 90, 39)).save(buffer, formato)
    return SimpleUploadedFile(nombre, buffer.getvalue())


class ValidarImagenTests(SimpleTestCase):
    def test_acepta_jpg_png_y_webp_reales(self):
        for nombre, formato in (("a.jpg", "JPEG"), ("a.png", "PNG"), ("a.webp", "WEBP")):
            validar_imagen_subida(imagen(nombre, formato))

    def test_rechaza_texto_con_extension_de_imagen(self):
        falsa = SimpleUploadedFile("foto.jpg", b"esto no es una imagen")
        with self.assertRaises(ValidationError):
            validar_imagen_subida(falsa)

    def test_rechaza_extension_no_permitida(self):
        with self.assertRaises(ValidationError):
            validar_imagen_subida(imagen("foto.gif", "GIF"))

    def test_rechaza_formato_real_distinto(self):
        with self.assertRaises(ValidationError):  # un GIF renombrado a .png
            validar_imagen_subida(imagen("foto.png", "GIF"))

    def test_rechaza_mas_de_5_mb(self):
        grande = SimpleUploadedFile("foto.jpg", b"0" * (5 * MB + 1))
        with self.assertRaises(ValidationError) as error:
            validar_imagen_subida(grande)
        self.assertEqual(error.exception.code, "imagen_grande")


class ConvertirTests(SimpleTestCase):
    def test_portada_16_9_en_webp_con_nombre_aleatorio(self):
        archivo = convertir_a_webp(imagen(tam=(1000, 1000)), TAM_PORTADA)
        self.assertTrue(archivo.name.endswith(".webp"))
        self.assertEqual(len(archivo.name), 32 + 5)
        with Image.open(io.BytesIO(archivo.read())) as resultado:
            self.assertEqual(resultado.format, "WEBP")
            self.assertEqual(resultado.size, TAM_PORTADA)

    def test_foto_cuadrada_desde_png_con_transparencia(self):
        buffer = io.BytesIO()
        Image.new("RGBA", (300, 500), (0, 0, 0, 0)).save(buffer, "PNG")
        archivo = convertir_a_webp(SimpleUploadedFile("a.png", buffer.getvalue()), TAM_FOTO)
        with Image.open(io.BytesIO(archivo.read())) as resultado:
            self.assertEqual(resultado.size, TAM_FOTO)
