from time import time
from tda.client import Client
from tda import auth
#from config_tda_api import account_id, client_id, api_key
import json
from datetime import datetime, timedelta
import pandas as pd
import requests
import pytz
import os

class TDADataService(Client):
    def __init__(self, api_key, token_file= os.path.join(os.path.dirname(__file__), 'tokens.json')):
        try:
            # Get New Access Token
            self._session = auth.client_from_token_file(token_file, api_key)
        except Exception as e:           
            print("Error in  of TDA Class:", e)

    def test_connection(self):
        print(f'Accessing Tradier Data with {self._key}')

    def get_intraday_history(self, symbol, time_period= 5, output_size=100, NDays=5, extended_hours = False):
        try:
            period = str(time_period)
            now = datetime.now()
            now_N_days_ago = now - timedelta(days= NDays)

            if period == '1': 
                    stock = self._session.get_price_history_every_minute(symbol, start_datetime=now_N_days_ago, end_datetime=now, need_extended_hours_data=extended_hours)
            if period == '5': 
                    stock = self._session.get_price_history_every_five_minutes(symbol, start_datetime=now_N_days_ago, end_datetime=now, need_extended_hours_data=extended_hours)
            if period == '10': 
                    stock = self._session.get_price_history_every_ten_minutes(symbol, start_datetime=now_N_days_ago, end_datetime=now, need_extended_hours_data=extended_hours)
            if period == '15': 
                    stock = self._session.get_price_history_every_fifteen_minutes(symbol, start_datetime=now_N_days_ago, end_datetime=now, need_extended_hours_data=extended_hours)
            if period == '30': 
                    stock = self._session.get_price_history_every_thirty_minutes(symbol, start_datetime=now_N_days_ago, end_datetime=now, need_extended_hours_data=extended_hours)

            stock_dict = stock.json()

            df = pd.DataFrame(stock_dict['candles'])
            if not df.empty:
                #print(df)
                df = df.assign(localtime = pd.to_datetime(df['datetime'], unit='ms'))
                df['localtime'] = df['localtime'].dt.tz_localize('UTC').dt.tz_convert('America/Chicago')
                #print(df)
                return df
            else:
                raise Exception('API returned empty dataframe')
        except Exception as e:
            print('Error in function tdameritrade_service.getintraday_history() : ',e)

    
    def get_latest_close(self, symbol, time_period=1):
        try:
            df = self.get_intraday_history(symbol, time_period,output_size=5)
            #print(df)
            out = float(df['close'].iloc[-1])
            #print(out)
            return out
        except Exception as e:
            print('Error in function tdameritrade_service.get_latest_close() : ',e)
    
    def get_quotes(self, symbols):
        try:
            response = self._session.get_quotes(symbols)
            response_str =  response.json()
            out = {}
            for symbol in symbols:
                if response_str[symbol]['assetType'] == 'FUTURE':
                    last_price = response_str[symbol]['lastPriceInDouble']
                else:
                    last_price = response_str[symbol]['lastPrice']
                out[symbol] = last_price
            return out
            
        except Exception as e:
            print('Error in function getQuotes: ',e)
    
    def get_current_day(self, offset=0):
        print(datetime.now())
        date = datetime.now(pytz.timezone('America/Chicago'))
        date = date - timedelta(days=offset)
        date_str = date.strftime("%Y-%m-%d")
        return date_str

    def OR_time_str_cst(self):
        today = self.get_current_day()
        OR_time_str = today + " " + "08:30:00-05:00"
        return OR_time_str

    def get_current_time_cst(self):
        time = datetime.now(pytz.timezone('America/Chicago')).strftime("%Y-%m-%d %H:%M:%S")
        return time

class TDADataServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, tda_client_key, **_ignored):
        if not self._instance:
            consumer_key = self.authorize(tda_client_key)
            self._instance = TDADataService(tda_client_key)
        return self._instance

    def authorize(self, key):
        return key


