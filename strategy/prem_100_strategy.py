import pandas as pd
import datetime
import os

class Prem100StrategyConfig:
    NAME = "Smart Straddle"
    DESC = "Straddle with Prem close to 100 at 9:30 am in Nifty"
    INSTRUMENT = 'BANKNIFTY'
    TRIGGER_PCT = 10
    SL_PCT = 30
    TARGET_PCT = None
    ENTRY_TIME = '9:30'
    ENTRY_LIMIT_TIME = '15:00' # No entry after this
    EXIT_TIME = '15:15'
    LOTS = 1
    LOT_SIZE = 25
    PLACE_ORDER = False

class Prem100Strategy:
    data = None
    api = None
    config = None
    current_position = 0
    entry_taken = 0
    data_path = "data/positions/"

    def __init__(self, config, api, data=None):
        self.api = api
        self.config = config
        self.api = api
        self.config = config
        self.quantity = self.config.LOTS*self.config.LOT_SIZE
        self.entry_time = datetime.time(int(self.config.ENTRY_TIME.split(':')[0]), int(self.config.ENTRY_TIME.split(':')[1]))
        self.entry_limit_time = datetime.time(int(self.config.ENTRY_LIMIT_TIME.split(':')[0]), int(self.config.ENTRY_LIMIT_TIME.split(':')[1]))
        self.exit_time = datetime.time(int(self.config.EXIT_TIME.split(':')[0]), int(self.config.EXIT_TIME.split(':')[1]))

        if data is None:
            self.prepare_data()

    def prepare_data(self):
        data = self.read_data()
        if data is None:
            data = self.api.get_option_chain(index=self.config.INSTRUMENT, n=10)
            data = self.filter_data(data)
            data = self.transform_data(data)
            self.data = data
            self.store_data()
        else:
            self.data = self.read_data()
        
    def filter_data(self, data):
        filtered_data = data[data["Price"] > 100]
        ce_data = filtered_data[filtered_data["OptionType"] == "CE"]
        pe_data = filtered_data[filtered_data["OptionType"] == "PE"]

        ce_data = ce_data[ce_data["Price"] == ce_data["Price"].min()]
        pe_data = pe_data[pe_data["Price"] == pe_data["Price"].min()]

        data = pd.concat([ce_data, pe_data])
        data = data.reset_index(drop=True)
        return data
    
    def transform_data(self, data):
        data["Date"] = datetime.datetime.now().date()
        data["Time"] = datetime.datetime.now().time()
        data["Instrument"] = self.config.INSTRUMENT
        data["Trigger Price"] = data["Price"] - data["Price"]*self.config.TRIGGER_PCT/100
        data["Stop Loss"] = data["Trigger Price"] + data["Trigger Price"]*self.config.SL_PCT/100
        data["Target"] = data["Trigger Price"] - data["Trigger Price"]*self.config.TARGET_PCT/100 if self.config.TARGET_PCT is not None else None
        data["Lots"] = self.config.LOTS
        data["Position"] = 0
        data["Entry Price"] = None
        data["Exit Price"] = None
        data["Current Price"] = None
        data["PNL"] = 0
        data["Order Id"] = None
        data["SL Order Id"] = None
        return data

    def update_ltp(self):
        for index, row in self.data.iterrows():
            ltp = self.api.get_ltp(exchange='NFO', token=row["Token"])
            self.data.at[index, "Current Price"] = ltp

            if row["Position"] == 1:
                self.data.at[index, "PNL"] = row["Entry Price"] - row["Current Price"]

    def is_time_to_enter(self):
        current_time = datetime.datetime.now().time()
        return (self.entry_time <= current_time <= self.entry_limit_time)

    def is_time_to_exit(self):
        current_time = datetime.datetime.now().time()
        return current_time > self.exit_time

    def process_for_trade(self):
        self.update_ltp()

        data_for_entry = self.data[(self.data["Entry Price"].isnull()) & (self.data["Current Price"] < self.data["Trigger Price"])]
        for index, row in data_for_entry.iterrows():
            self.enter_trade(index, row)
            self.store_data()

        data_for_exit = self.data[(self.data["Position"] == 1) & (self.data["Current Price"] > self.data["Stop Loss"])]
        for index, row in data_for_exit.iterrows():
            self.exit_trade(index, row)
            self.store_data()

        if self.is_time_to_exit():
            data_with_positions = self.data[self.data["Position"] == 1]
            for index, row in data_with_positions.iterrows():
                self.exit_trade(index, row)
            self.store_data()

    def enter_trade(self, index, row):
        order_id = self.place_order(row)
        self.data.at[index, "Entry Price"] = row["Current Price"]
        self.data.at[index, "Position"] = 1
        self.data.at[index, "Order Id"] = order_id
        print(f'Entry for Strike: {row["StrikePrice"]}{row["OptionType"]}@{row["Current Price"]}')

    def exit_trade(self, index, row):
        print(f'Exit for Strike: {row["StrikePrice"]}{row["OptionType"]}@{row["Current Price"]}')
        self.data.at[index, "Exit Price"] = row["Current Price"]
        self.data.at[index, "Position"] = 0

    def place_order(self, row):
        order_id = 123456
        print(f'Place order for Strike: {row["StrikePrice"]}{row["OptionType"]}@{row["Current Price"]}')
        return order_id

    # def place_order(api, buy_or_sell, trading_symbol, quantity):
    #     order = api.place_order(buy_or_sell=buy_or_sell, product_type='I', exchange='NFO', tradingsymbol=trading_symbol,
    #                             quantity=quantity, discloseqty=0, price_type='MKT', price=0, trigger_price=None,
    #                             retention='DAY', remarks='smart_straddle')
    #     order_id = order['norenordno']
    #     print(f"Order Placed - {order_id}")
    #     return order_id
    
    def get_data(self):
        return self.data

    def update_data(self, data):
        self.data = data

    def store_data(self):
        path = f'{self.data_path}{datetime.datetime.now().date()}_positions.feather'
        self.data.to_feather(path)

    def read_data(self):
        path = f'{self.data_path}{datetime.datetime.now().date()}_positions.feather'
        if os.path.exists(path):
            return pd.read_feather(path)
        else:
            return None

    def get_all_positions(self):
        data = None
        if os.path.exists(self.data_path):
            files = os.listdir(self.data_path)
            for file in files:
                file_path = f"{self.data_path}/{file}"
                if data is None:
                    data = pd.read_feather(file_path)
                else:
                    data = pd.concat([data, pd.read_feather(file_path)], ignore_index=True)
        
        data = data[data["Entry Price"].notnull()]
        return data