from brokers.shoonya_api import ShoonyaApiPy
from apscheduler.schedulers.blocking import BlockingScheduler
from strategy.prem_100_strategy import Prem100Strategy, Prem100StrategyConfig
import pytz
from tabulate import tabulate

current_timezone = 'Asia/Kolkata'
tz = pytz.timezone(current_timezone)

sched = BlockingScheduler(timezone=tz, job_defaults={'max_instances': 20})

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=14, minute=19)
def prepare_data():
    api = ShoonyaApiPy()
    prem_strategy = Prem100Strategy(Prem100StrategyConfig, api, None)
    sched.add_job(enter_trade_job, 'interval', seconds=1, args=[api, prem_strategy], id='enter_trade')
    sched.add_job(track_data, 'interval', seconds=30, args=[prem_strategy], id='display_data')

def enter_trade_job(api: ShoonyaApiPy, prem_strategy: Prem100Strategy):
    prem_strategy.process_for_trade()

def track_data(prem_strategy: Prem100Strategy):
    data = prem_strategy.get_data()
    data = data[["StrikePrice", "OptionType", "Price", "Position", "Current Price", "Trigger Price", "Entry Price", "Exit Price", "Stop Loss", "PNL"]]
    print(tabulate(data, headers='keys', tablefmt='psql'))
    print()
    print(f"Total PNL = {data['PNL'].sum() * prem_strategy.config.LOT_SIZE:.2f}")
    print()

if __name__ == "__main__":
    sched.start()