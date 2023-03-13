from brokers.shoonya_api import ShoonyaApiPy
from apscheduler.schedulers.blocking import BlockingScheduler
from strategy.prem_100_strategy import Prem100Strategy, Prem100StrategyConfig
import pytz
from tabulate import tabulate
import position_file_handler as fh
import datetime

current_timezone = 'Asia/Kolkata'
tz = pytz.timezone(current_timezone)
exit_time = datetime.time(15, 30)

sched = BlockingScheduler(timezone=tz, job_defaults={'max_instances': 20})

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=18, minute=10)
def prepare_data():
    api = ShoonyaApiPy()
    prem_strategy = Prem100Strategy(Prem100StrategyConfig, api, None)
    sched.add_job(execute_trade_job, 'interval', seconds=1, args=[api, prem_strategy], id='execute_trade')
    sched.add_job(track_data, 'interval', seconds=30, args=[prem_strategy], id='track_trade_job')

def stop_running_job():
    ext_trade_job = sched.get_job("execute_trade")
    track_trade_job = sched.get_job("track_trade_job")
    if ext_trade_job:
        sched.remove_job('execute_trade')

    if track_trade_job:
        sched.remove_job('track_trade_job')

def execute_trade_job(api: ShoonyaApiPy, prem_strategy: Prem100Strategy):
    prem_strategy.process_for_trade()

def track_data(prem_strategy: Prem100Strategy):
    data = prem_strategy.get_data()
    data["Strike"] = data['StrikePrice'].astype(str).str.cat(data['OptionType'])
    data = data[["Strike", "Price", "Position", "Current Price", "Trigger Price", "Entry Price", "Exit Price", "Stop Loss", "PNL"]]
    
    print(tabulate(data, headers='keys', tablefmt='psql'))
    print(f"Total PNL = {data['PNL'].sum() * prem_strategy.config.LOT_SIZE:.2f}")

    if ((data["Entry Price"].count() > 0) & (data["Position"].sum() == 0)) | \
    ((data["Entry Price"].count() == 0) & (datetime.datetime.now().astimezone(tz).time() > exit_time)):
        print("All positions exited or time is 3:30 pm. Hence stoipping the jobs")
        stop_running_job()

if __name__ == "__main__":
    sched.start()