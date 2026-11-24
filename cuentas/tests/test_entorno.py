"""Pruebas de la lectura de configuración desde .env (config/entorno.py)."""

import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.entorno import booleano, lista, variable


class VariableTests(SimpleTestCase):
    def test_variable_obligatoria_ausente_dice_cual_falta(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesMessage(ImproperlyConfigured, "Falta la variable DB_NAME"):
                variable("DB_NAME", obligatoria=True)

    def test_variable_vacia_cuenta_como_ausente(self):
        with mock.patch.dict(os.environ, {"SECRET_KEY": "   "}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                variable("SECRET_KEY", obligatoria=True)

    def test_variable_opcional_usa_el_defecto(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(variable("DB_PORT", "5432"), "5432")

    def test_variable_quita_espacios(self):
        with mock.patch.dict(os.environ, {"DB_HOST": "  localhost "}, clear=True):
            self.assertEqual(variable("DB_HOST"), "localhost")


class BooleanoYListaTests(SimpleTestCase):
    def test_booleano_acepta_varias_formas(self):
        for texto in ("True", "true", "1", "sí", "on"):
            with mock.patch.dict(os.environ, {"DEBUG": texto}, clear=True):
                self.assertTrue(booleano("DEBUG"), texto)
        for texto in ("False", "0", "no"):
            with mock.patch.dict(os.environ, {"DEBUG": texto}, clear=True):
                self.assertFalse(booleano("DEBUG"), texto)

    def test_booleano_sin_valor_usa_el_defecto(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(booleano("DEBUG"))
            self.assertTrue(booleano("DEBUG", defecto=True))

    def test_lista_separa_por_comas_y_quita_vacios(self):
        with mock.patch.dict(os.environ, {"ALLOWED_HOSTS": "a.com, b.com,,"}, clear=True):
            self.assertEqual(lista("ALLOWED_HOSTS"), ["a.com", "b.com"])
