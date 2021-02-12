
import csv

from django.db import connection, transaction
from django.http import HttpResponse, HttpResponseBadRequest

from rest_framework.views import APIView
from rest_framework.response import Response

from rest_pandas import PandasView

from app.service import store_csv_file, get_display_dataframe, get_electric_plants, extract_start_and_end_time

class Store(APIView):

    def post(self, request, format=None):
        file = request.FILES['file']
        try:
            duplicate_count = store_csv_file(file)
            is_successfully_uploaded = True
        except (ValueError, KeyError) as e:
            print(e)
            is_successfully_uploaded = False
            duplicate_count = -1
        data = {
            "is_success": is_successfully_uploaded,
            "duplicate_count": duplicate_count
        }
        return Response(data)

from rest_framework_csv import renderers as r

class Display(APIView):

    def get(self, request, format=None):
        try:
            time_window = request.query_params.get('time_window')
            start_time, end_time = extract_start_and_end_time(time_window)
            powerplants = get_electric_plants(self.request.query_params.getlist('electric_plant_list'))
        except ValueError as e:
            return HttpResponseBadRequest(e)
        df = get_display_dataframe(start_time, end_time, powerplants)
        response = self.generate_response_from_df(df)
        return response


    def generate_response_from_df(self, df):
        csv_dict = df.to_dict('records')
        column_names = df.columns.values.tolist()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'
        writer = csv.DictWriter(response, fieldnames=column_names)
        writer.writeheader()
        for i in csv_dict:
            writer.writerow(i)
        return response
