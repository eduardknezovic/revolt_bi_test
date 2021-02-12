from django.test import TestCase

from rest_framework.test import APIClient

from app.models import PowerPlant, PowerPlantInfo
from app.service import parse_csv_columns, get_or_create_powerplant

import pathlib
from io import StringIO, BytesIO

import pandas as pd

class UnitTestCase(TestCase):

    def test_get_or_create_powerplant(self):
        PowerPlant.objects.all().delete()
        powerplant_names = ["temelin", "temelin", "dukovany", "temelin"]
        for powerplant_name in powerplant_names:
            obj = get_or_create_powerplant(powerplant_name)
            assert obj.name == powerplant_name
        stored_powerplants = [powerplant.name for powerplant in PowerPlant.objects.all()]
        assert stored_powerplants == ["temelin", "dukovany"]

    def test_columns_parser(self):
        columns = [
            "utc_timestamp", "temelin_actual", "temelin_installed",
            "dukovany_actual", "dukovany_installed", "pocerady_actual",
            "pocerady_installed"
        ]
        grouped_columns = parse_csv_columns(columns)
        assert grouped_columns == {
            'temelin': ['utc_timestamp', 'temelin_actual', 'temelin_installed'],
            'dukovany': ['utc_timestamp', 'dukovany_actual', 'dukovany_installed'],
            'pocerady': ['utc_timestamp', 'pocerady_actual', 'pocerady_installed']
        }

