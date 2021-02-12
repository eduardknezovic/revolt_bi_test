
from django.test import TestCase

from rest_framework.test import APIClient

from app.models import PowerPlant, PowerPlantInfo
from app.service import parse_csv_columns, get_or_create_powerplant

import pathlib
from io import StringIO, BytesIO

import pandas as pd

class BaseTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.data_directory = pathlib.Path(__file__).parent.absolute() / 'data'

    def store(self, filepath):
        with open(filepath, 'r') as f:
            data = {
                'file': f
            }
            response = self.client.post('/store/', data=data, format='multipart')
        return response

    def store_valid_input(self, filename, expected_duplicate_count, expected_before_count=None, expected_after_count=None):
        if expected_before_count:
            assert PowerPlantInfo.objects.count() == expected_before_count
        filepath = self.data_directory / filename

        response = self.store(filepath)

        assert response.status_code == 200
        assert response.data == {
            'is_success': True,
            'duplicate_count': expected_duplicate_count
        }
        after_count = PowerPlantInfo.objects.count()
        if expected_after_count:
            assert expected_after_count == after_count
        return after_count


    def display(self, time_window, electric_plants, expected_status_code, expected_output_filename = None):
        query_params = {
            'time_window': time_window,
            'electric_plant_list': electric_plants
        }
        response = self.client.get('/display/', query_params)
        assert response.status_code == expected_status_code
        if response.status_code == 400:
            return
        output = pd.read_csv(BytesIO(response.content))
        if expected_output_filename:
            input = pd.read_csv(self.data_directory / expected_output_filename)
            assert output.equals(input)
