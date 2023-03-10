import util
from os import path
import feather

def save_position_file(name, data):
    feather.write_dataframe(data, get_position_file_path(name))

def position_file_exist(name):
    return path.exists(get_position_file_path(name))

def read_position_file(name):
    data = feather.read_dataframe(get_position_file_path(name))
    return data

def get_position_file_path(name):
    today_date, _ = util.get_current_date_time()
    file_path = f'data/positions/{name.lower()}_{today_date}.feather'
    return file_path