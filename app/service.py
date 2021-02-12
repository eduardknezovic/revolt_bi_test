
import re
import pandas as pd

from app.models import PowerPlant, PowerPlantInfo
from django.db import connection, transaction

def extract_start_and_end_time(time_window_string):
    import datetime
    expected_format_message = "Expected format: \"yyyy-mm-dd HH:MM:SS - yyyy-mm-dd HH:MM:SS\""
    if not time_window_string:
        raise ValueError("Time window missing! " + expected_format_message)
    time_window_as_list = [i.strip() for i in time_window_string.strip().split(" - ")]
    if len(time_window_as_list) != 2:
        raise ValueError("Time window is not correct! " + expected_format_message)
    for t in time_window_as_list:
        try:
            datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        except:
            raise ValueError("Wrong time_window format! " + expected_format_message)
    return time_window_as_list


def get_electric_plants(electric_plant_names):
    powerplants = PowerPlant.objects.filter(name__in=electric_plant_names)
    if powerplants.count() != len(electric_plant_names):
        raise ValueError("Tried looking for nonexisting powerplants!!")
    return powerplants




def get_display_dataframe(start_timestamp, end_timestamp, powerplants):
    """
    Takes all powerplants, its records and generates a csv file

    Returns a csv file for the HttpResponse
    """
    powerplant_to_dataframe = {
        powerplant.name: PowerPlantInfo.get_items_as_dataframe(start_timestamp, end_timestamp, powerplant)
        for powerplant in powerplants
    }
    dfs = list(powerplant_to_dataframe.values())
    merged_dfs = merge_all_dataframes(dfs)
    merged_dfs = merged_dfs.fillna("")
    return merged_dfs


def merge_all_dataframes(dfs):
    dfs = [df.set_index('utc_timestamp') for df in dfs]
    return pd.concat(dfs, axis=1).reset_index()
    

def drop_duplicates(df):
    new_df = df.drop_duplicates(subset=['utc_timestamp'], keep=False)
    return new_df, df.shape[0] - new_df.shape[0]

def drop_duplicates_that_exist_in_database(df, powerplant):
    if not df.shape[0]:
        return df, 0
    min_timestamp = df.iloc[0]["utc_timestamp"]
    max_timestamp = df.iloc[-1]["utc_timestamp"]
    timestamps_from_db = PowerPlantInfo.get_all_timestamps_in_interval(min_timestamp, max_timestamp, powerplant)
    timestamps_from_db = list(timestamps_from_db)
    timestamps_from_db = [str(i) for i in timestamps_from_db]
    new_df = remove_timestamps_from_df(df, timestamps_from_db)
    dupes = df.shape[0] - new_df.shape[0]
    return new_df, dupes


def remove_timestamps_from_df(df, timestamps):
    df = df.drop(df[df.utc_timestamp.isin(timestamps)].index)
    return df

def drop_empty(df):
    return df.dropna(subset=['actual', 'installed'])

def store_csv_file(csv_file):
    df = pd.read_csv(csv_file)
    df = df.rename(columns=lambda x: x.strip())
    df = df.sort_values(by=["utc_timestamp"])
    powerplant_name_to_columns = parse_csv_columns(df.columns)
    duplicate_count = 0
    for powerplant_name, columns in powerplant_name_to_columns.items():
        records = df[columns]
        records = records.rename(columns=remove_powerplant_name_from_column_name)
        records, i = drop_duplicates(records)
        duplicate_count += i
        records = drop_empty(records)
        powerplant = get_or_create_powerplant(powerplant_name)
        records, i = drop_duplicates_that_exist_in_database(records, powerplant)
        duplicate_count += i
        records["powerplant"] = powerplant
        d = records.to_dict('records')
        PowerPlantInfo.objects.bulk_create(
            (
                PowerPlantInfo(**record)
                for record in d
            )
        )
    return duplicate_count

def remove_powerplant_name_from_column_name(column_name):
    """
    Alters the column name from xxx_actual to xxx or yyy_installed to installed
    """
    if "_actual" in column_name:
        return "actual"
    if "_installed" in column_name:
        return "installed"
    return column_name

def get_or_create_powerplant(powerplant_name):
    obj, created = PowerPlant.objects.get_or_create(name=powerplant_name)
    return obj

def create_model_instances(powerplant, records):
    model_instances = [PowerPlantInfo(
        powerplant=powerplant,
        **record
    ) for record in records]
    return model_instances

def parse_csv_columns(columns):
    result = {}
    time_column = columns[0]
    assert time_column == "utc_timestamp"
    grouped_columns = zip(columns[1::2], columns[2::2])
    for actual_column, installed_column in grouped_columns:
        assert re.match("^(\w+)_actual$", actual_column)
        assert re.match("^(\w+)_installed$", installed_column)
        assert extract_powerplant_name_from_column_name(actual_column) == extract_powerplant_name_from_column_name(installed_column)
        powerplant_name = extract_powerplant_name_from_column_name(actual_column)
        result[powerplant_name] = [time_column, actual_column, installed_column]
    return result

def extract_powerplant_name_from_column_name(column_name):
    items = re.findall("^(\w+)_\w+", column_name)
    assert len(items) == 1
    return items[0]






