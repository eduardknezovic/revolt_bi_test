from django.test import TestCase

from rest_framework.test import APIClient

from app.models import PowerPlant, PowerPlantInfo
from app.service import parse_csv_columns, get_or_create_powerplant

import pathlib
from io import StringIO, BytesIO

import pandas as pd

from app.tests.base import BaseTestCase

class PerformanceTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.time_window = '2020-04-01 20:00:00 - 2020-08-02 20:00:00'
        self.electric_plants = ["powerplant1", "powerplant2", "powerplant3", "powerplant4", "powerplant5", "powerplant6"]

    def test_performance(self):
        current_count = self.store_valid_input('performance_input.csv', 0, expected_before_count=0)
        current_count = self.store_valid_input('performance_input.csv', current_count, expected_before_count=current_count, expected_after_count=current_count)
        self.display(self.time_window, self.electric_plants, 200, 'performance_input.csv')
        current_count = self.store_valid_input('performance_input_3_duplicates_in_file.csv', current_count * 3, expected_before_count=current_count, expected_after_count=current_count)
        self.display(self.time_window, self.electric_plants, 200, 'performance_input.csv')

