from datetime import datetime, date
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from NorenRestApiPy.NorenApi import NorenApi
import pyotp
import os


class Credentials:
    user    = 'FA77509'
    pwd     = 'Rakesh@28776'
    vc      = 'FA77509_U'
    app_key = '5ee05fb0bdc4360a6bbb6bf67cb1efb7'
    imei    = 'abc1234'
    token   = 'B4PB6QSC7C5L452Y5KI35JO5R7HKN355'

class ShoonyaApiPy(NorenApi):
    token = None
    token_file_path = "/Users/rakesh/Trade/Shoonya/token.txt"
    fno_symbols = None
    nse_symbols = None
    index_base = {'NIFTY': 50, 'BANKNIFTY':100}
    index_token = {'NIFTY':'26000', 'BANKNIFTY':'26009'}
    index_ltp = None
    
    def __init__(self):
        NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/', eodhost='https://shoonya.finvasia.com/chartApi/getdata/')
        self.generate_token()
        self.login_shoonya()
        
    def generate_token(self):
        print("Generating a new token")
        self.token = pyotp.TOTP(Credentials.token).now()
        
    def login_shoonya(self):
        user_details = self.login(userid=Credentials.user, password=Credentials.pwd, twoFA=self.token, vendor_code=Credentials.vc, api_secret=Credentials.app_key, imei=Credentials.imei)
        
    def get_fno_symbols(self):
        if self.fno_symbols is None:
            nfo_link = "https://shoonya.finvasia.com/NFO_symbols.txt.zip"
            symbol_df = pd.read_csv(nfo_link)
            symbol_df['Expiry'] = pd.to_datetime(symbol_df['Expiry']).apply(lambda x: x.date())
            self.fno_symbols = symbol_df
        return self.fno_symbols
    
    def get_nse_symbols(self):
        if self.nse_symbols is None:
            nse_link = "https://shoonya.finvasia.com/NSE_symbols.txt.zip"
            symbol_df = pd.read_csv(nse_link)
            self.nse_symbols = symbol_df
        return self.nse_symbols
    
    def get_instrument_token(self, instrument):
        if self.index_token.get(instrument) is not None:
            return self.index_token.get(instrument)
        else:
            symbol_df = self.get_nse_symbols()
            symbol_df = symbol_df[symbol_df['Symbol'] == instrument]
            return str(symbol_df['Token'].values[0])
    
    def get_fno_symbols_for_instrument(self, instrument, expiry=None):
        symbol_df = self.get_fno_symbols()
        symbol_df = symbol_df[symbol_df['Symbol']==instrument]
        if expiry is None:
            now = datetime.now()
            if (now.date() == symbol_df['Expiry'].min()) and (now.time().hour > 14):
                symbol_df = symbol_df[symbol_df['Expiry'] != symbol_df['Expiry'].min()]
            data = symbol_df[symbol_df['Expiry'] == symbol_df['Expiry'].min()]
        return data
    
    def get_fno_symbols_from_atm(self, index, n):
        data = self.get_fno_symbols_for_instrument(index)
        ce_data = data[data['OptionType'] == 'CE'].sort_values(by=['StrikePrice'], ascending=False)
        base = int(ce_data.iloc[int(len(ce_data)/2)]['StrikePrice'] - ce_data.iloc[int(len(ce_data)/2)+1]['StrikePrice'])
        data['StrikePrice'] = data['StrikePrice'].astype(int)
        data['Token'] = data['Token'].astype(str)
        atm = self.get_instrument_atm(index, base)
        data = data[(data['StrikePrice'] <= atm + n*base) & (data['StrikePrice'] >= atm - n*base)]
        return data
    
    def get_index_ltp(self, index):
        exchange='NSE'
        token = self.index_token.get(index)
        return self.get_ltp(exchange, token)
    
    def get_ltp(self, exchange, token):
        data = self.get_quotes(exchange=exchange, token=token)
        ltp = float(data.get('lp'))
        return ltp
    
    def get_index_atm(self, index):
        exchange = 'NSE'
        ltp = self.get_index_ltp(index)         
        base = self.index_base.get(index)    
        atm = self.calculate_atm(ltp, base)
        return atm
    
    def get_instrument_atm(self, instrument, base):
        exchange = 'NSE'
        token = self.get_instrument_token(instrument)
        ltp = self.get_ltp(exchange, token)   
        atm = self.calculate_atm(ltp, base)
        return atm
    
    def calculate_atm(self, ltp, base):
        a = (ltp//base) * base
        b = a + base
        return int(b if ltp - a > b - ltp else a)
    
    def update_option_chain_with_price(self, row):
        quote = self.get_quotes(exchange=row['Exchange'], token=row['Token'])
        price = float(quote.get('lp'))
        oi = int(quote.get('oi')) if 'oi' in quote else None
        data = {"Exchange": row["Exchange"], "TradingSymbol": row["TradingSymbol"], "OptionType": row["OptionType"], 
                "StrikePrice": int(row["StrikePrice"]), "Price": price, "OI": oi, "Token": row['Token'], "LotSize": row['LotSize']}
        return data
    
    def get_option_chain(self, index, n=20):
        symbol_df = self.get_fno_symbols_from_atm(index, n)
        data = symbol_df.to_json(orient='records')
        data = json.loads(data)
        oi_data = []
        with ThreadPoolExecutor(15) as executor:
            for result in executor.map(self.update_option_chain_with_price, data):
                oi_data.append(result)

        oi_df = pd.DataFrame(oi_data)
        return oi_df

    def place_order(self, row):
        pass
    
    def current_positions(self):
        all_positions = []
        positions = self.get_positions()
        for position in positions:
            position_dict = order_hist = {'Symbol': position['tsym'], 'Token': position["token"], 'Qty': position['netqty'], 
            'Price': position['netavgprc'], 'Current_Price': position['lp']}
            all_positions.append(position_dict)
        return all_positions
