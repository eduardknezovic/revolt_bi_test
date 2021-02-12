
import pathlib
from io import StringIO, BytesIO
import pandas as pd

from django.test import TestCase

from rest_framework.test import APIClient

from app.models import PowerPlant, PowerPlantInfo
from app.service import parse_csv_columns, get_or_create_powerplant

from app.tests.base import BaseTestCase

def send_file_to_server(client, filepath, expected_status_code=200):
    files = {'file': open(filepath, 'r')}
    response = client.post('/store/', data=files, format='multipart')
    assert response.status_code == expected_status_code
    files['file'].close()
    return response.data

# Create your tests here.
class OurTestCase(BaseTestCase):

    def test_get_bad_requests(self):
        client = APIClient()

        # Nonexisting powerplants
        self.display('2050-05-01 20:00:00 - 2051-05-01 21:00:00', ["temelin", "dukovany"], 400)
        # Nonexisting params
        self.display("", [], 400)
        # Invalid time_window
        self.display('bad time format - 2051-05-01 21:00:00', ["temelin", "dukovany"], 400)
        # Invalid delimiter
        self.display('2050-05-01 20:00:00-2051-05-01 21:00:00', ["temelin", "dukovany"], 400)
        current_count = self.store_valid_input('input1.csv', 0, expected_before_count=0, expected_after_count=9)
        self.display('2020-04-01 20:00:00 - 2020-08-02 20:00:00', ["temelin", "dukovany", "pocerady", "nonexisting_powerplant"], 400)
        self.display('2020-04-01 - 2020-08-02 20:00:00', ["temelin", "dukovany", "pocerady"], 400)

        assert PowerPlantInfo.objects.count() == 9
        response_data = send_file_to_server(client, self.data_directory / 'bad_input1.csv', 200)
        assert response_data == {
            'is_success': False,
            'duplicate_count': -1
        }
        assert PowerPlantInfo.objects.count() == 9


    def test_api_empty_display(self):
        self.store_valid_input('input1.csv', 0, expected_before_count=0, expected_after_count=9)
        self.display('2050-05-01 20:00:00 - 2051-05-01 21:00:00', ["temelin", "dukovany"], 200, 'expected_empty_output.csv')

    def test_api(self):
        current_count = self.store_valid_input('input1.csv', 0, expected_before_count=0, expected_after_count=9)
        current_count = self.store_valid_input('input1.csv', current_count, expected_after_count=current_count)
        current_count = self.store_valid_input('input2.csv', 12)
        self.display('2020-05-01 20:00:00 - 2020-05-02 20:00:00', ["temelin", "dukovany", "pocerady"], 200, 'expected_output.csv')
        self.display('2020-05-01 20:00:00 - 2020-05-01 21:00:00', ["temelin", "dukovany"], 200, 'expected_filtered_output.csv')
        current_count = self.store_valid_input('input_temelin_only.csv', 0, expected_after_count=14)
        self.display('2020-04-01 20:00:00 - 2020-08-02 20:00:00', ["temelin", "dukovany", "pocerady"], 200, 'expected_output_with_empty_values.csv')
        current_count = self.store_valid_input('input_pocerady_only.csv', 0, expected_after_count=15)
        self.display('2020-04-01 20:00:00 - 2020-08-02 20:00:00', ["temelin", "dukovany", "pocerady"], 200, 'expected_output_with_empty_values_2.csv')
        current_count = self.store_valid_input('input3.csv', 0, expected_after_count=22)

