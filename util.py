import math
import pendulum
from tabulate import tabulate
from datetime import datetime
import pytz
import logging

ind_timezone = 'Asia/Kolkata'
tz = pytz.timezone(ind_timezone)
time_format = 'DD-MMMM HH:mm A'
LOG_FILE_NAME = f'logs/Log_{pendulum.now(ind_timezone).format("DD-MMM-YY")}.log'
logging.basicConfig(format='%(asctime)s: %(message)s', datefmt='%d-%b %H:%M')
# logging.basicConfig(format='%(asctime)s: %(message)s', datefmt='%d-%b %H:%M', filename=LOG_FILE_NAME, filemode='a')

display_data = lambda x: print(tabulate(x, headers='keys', tablefmt='psql'))

def round_up_to_nearest_100(num):
    return math.ceil(num / 100) * 100

def round_to_nearest_100(num):
    return round(num, -2)

def atm_strike(ltp, base):
    a = (ltp//base) * base
    b = a + base
    return int(b if ltp - a > b - ltp else a)

def log_data(messg):
    logging.warning(messg)

def convert_millis(millis):
    seconds=(millis/1000)%60
    minutes=(millis/(1000*60))%60
    hours=(millis/(1000*60*60))%24
    return seconds, minutes, hours

# Return: today date (dd-mm-yyyy) and current time (hh:mm) [India TZ]
def get_current_date_time():
    now = datetime.now(tz)
    today_date = now.strftime("%d-%m-%Y")
    current_time = now.strftime("%H:%M")
    return today_date, current_time