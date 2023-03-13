from os import path
import feather
import datetime

def save_position_file(data):
    feather.write_dataframe(data, get_position_file_path())

def position_file_exist():
    return path.exists(get_position_file_path())

def read_position_file():
    data = feather.read_dataframe(get_position_file_path())
    return data

def get_position_file_path():
    today_date = datetime.datetime.now().date()
    file_path = f'data/positions/{today_date}_positions.feather'
    return file_path