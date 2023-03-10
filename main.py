from brokers.shoonya_api import ShoonyaApiPy
from apscheduler.schedulers.blocking import BlockingScheduler
from strategy.prem_100_strategy import Prem100Strategy, Prem100StrategyConfig
import pytz
import json
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from tabulate import tabulate
import os
import datetime

current_timezone = 'Asia/Kolkata'
tz = pytz.timezone(current_timezone)

class Cache:
    def __init__(self) -> None:
        self.data = None
        self.entry = []
        self.exit = []

    def update_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

cache = Cache()
sched = BlockingScheduler(timezone=tz, job_defaults={'max_instances': 20})

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=17, minute=28)
def prepare_data():
    api = ShoonyaApiPy()
    # data = api.get_option_chain(index='NIFTY', n=2)
    prem_strategy = Prem100Strategy(Prem100StrategyConfig, api, None)
    sched.add_job(enter_trade_job, 'interval', seconds=1, args=[api, prem_strategy], id='enter_trade')
    sched.add_job(track_data, 'interval', seconds=30, args=[prem_strategy], id='display_data')
    position = api.current_positions()
    print(position)

def enter_trade_job(api: ShoonyaApiPy, prem_strategy: Prem100Strategy):
    prem_strategy.process_for_trade()

def track_data(prem_strategy: Prem100Strategy):
    # os.system('clear')
    data = prem_strategy.get_data()
    data = data[["StrikePrice", "OptionType", "Price", "Position", "Current Price", "Trigger Price", "Entry Price", "Exit Price", "Stop Loss", "PNL"]]
    print(tabulate(data, headers='keys', tablefmt='psql'))
    print()
    date_time = f"{datetime.datetime.now()}"
    print(f"Total PNL = {data['PNL'].sum() * prem_strategy.config.LOT_SIZE:.2f}")
    print()
    # positions = prem_strategy.get_all_positions()
    # positions = positions[["StrikePrice", "OptionType", "Price", "Position", "Current Price", "Trigger Price", "Entry Price", "Exit Price", "Stop Loss", "PNL"]]
    # print(tabulate(positions, headers='keys', tablefmt='psql'))
    # print()
    # date_time = f"{datetime.datetime.now()}"
    # print(f"Total PNL = {positions['PNL'].sum() * prem_strategy.config.LOT_SIZE:.2f}")

if __name__ == "__main__":
    sched.start()