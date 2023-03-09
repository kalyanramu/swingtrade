#---------------References------------------------------------------------------------------------------------------#
# Decorators : https://medium.com/better-programming/how-to-refresh-an-access-token-using-decorators-981b1b12fcb9---#
# Technical Indicators: https://github.com/Crypto-toolbox/pandas-technical-indicators/blob/master/technical_indicators.py

#-------------------------------------------------------------------------------------------------------------------#

from tda.client import Client
from tda import auth
from config_tda_api import account_id, client_id, api_key
import json
from datetime import datetime, timedelta
import pandas as pd
import requests

class TDA(Client):
    BASE = 'https://api.tdameritrade.com/v1/'
    quotes_url = 'https://api.tdameritrade.com/v1/marketdata/quotes'
    history_url = BASE + 'marketdata/{}/pricehistory'
    access_token = None
    access_token_expiration = None
    token_info = None

    def __init__(self, token_file="tokens.json"):
        try:
            # Get New Access Token
            self._session = auth.client_from_token_file(token_file, api_key)
        except Exception as e:           
            print("Error in  of TDA Class:", e)

    def historyDF_minutes(self, symbol, period = '5', NDays = 5, extended_hours = False):
        try:
            now = datetime.now()
            now_N_days_ago = now - timedelta(days= NDays)

            if period == '1': 
                    stock = self._session.get_price_history_every_minute(symbol,    start_datetime=now_N_days_ago, end_datetime=now, need_extended_hours_data=extended_hours)
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
                print(df)
                df = df.assign(localtime = pd.to_datetime(df['datetime'], unit='ms'))
                df['localtime'] = df['localtime'].dt.tz_localize('UTC').dt.tz_convert('America/Chicago')
                #print(df)
                return df
            else:
                raise Exception('API returned empty dataframe')
        except Exception as e:
            print('Error in function historyDF_minutes: ',e)

    def get_current_time(self):
        try:
            response = self._session.get_quote('SPY')
            json_response = response.json()
            #print(json_response)
            curr_time = json_response['SPY']['quoteTimeInLong']
            #print(curr_time)
            return curr_time
        except Exception as e:
            print('Error in function get_curr_time: ',e)

    def getOptionChain(self,symbol, expDate=None, option_dir = 'CALL', from_date = None, to_date = None):
        try:
            if option_dir == 'CALL':
                out = self._session.get_option_chain(symbol, contract_type = Client.Options.ContractType.CALL, from_date=from_date, to_date=to_date)
            elif option_dir == 'PUT':
                out = self._session.get_option_chain(symbol, contract_type = Client.Options.ContractType.PUT, from_date=from_date, to_date=to_date)
            else:
                out = self._session.get_option_chain(symbol)

            query = out.json()
            #print(query)
            big_dict = []
            for contr_type in ['callExpDateMap', 'putExpDateMap']:
                contract = dict(query)[contr_type]
                expirations = contract.keys()
                for expiry in list(expirations):
                    strikes = contract[expiry].keys()
                    for st in list(strikes):
                        entry = contract[expiry][st][0]
                        big_dict.append(entry)
            df = pd.DataFrame(big_dict)
            return df
        except Exception as e:
            print('Error in function getOptionChain: ',e)


    def getHighestVolOption(self,symbol, expDate=None, option_dir = 'CALL', from_date = None, to_date = None):
        try:
            df = self.getOptionChain(symbol, expDate=expDate, option_dir = option_dir, from_date = from_date, to_date = to_date)
            max_row = df.loc[df['totalVolume'].idxmax()]
            #print(max_row)
            strikePrice = max_row['strikePrice']
            askPrice = max_row['ask']
            oi = max_row['openInterest']
            strike_symbol = max_row['symbol']
            Volume = max_row['totalVolume']
            print("{} has max Volume at Strike : {}, AskPrice: {}, OI : {}, Volume: {} ".format(symbol,strikePrice, askPrice, oi, Volume))
            return max_row
        except Exception as e:
            print('Error in function getHighestVolOption: ',e)

    def getHighestOIOption(self,symbol, expDate=None, option_dir = 'CALL', from_date = None, to_date = None):
        try:
            df = self.getOptionChain(symbol, expDate=expDate, option_dir = option_dir, from_date = from_date, to_date = to_date)
            max_row = df.loc[df['openInterest'].idxmax()]
            #print(max_row)
            strikePrice = max_row['strikePrice']
            askPrice = max_row['ask']
            oi = max_row['openInterest']
            Volume = max_row['totalVolume']
            print("{} has max OI at Strike : {}, AskPrice: {}, OI : {}, Volume: {} ".format(symbol,strikePrice, askPrice, oi, Volume))
            return max_row
        except Exception as e:
            print('Error in function getHighestOIOption: ',e)

    def getOptionGoodSpread(self,symbol, expDate=None, option_dir = 'CALL', from_date = None, to_date = None):
        try:
            df = self.getOptionChain(symbol, expDate=expDate, option_dir = option_dir, from_date = from_date, to_date = to_date)
            #otm_rows = df.loc[df['inTheMoney'] == False]
            #print(otm_rows)

            otm_rows = df.loc[(df['bid'] >=2) & (df['bid'] <=5)].copy()
            otm_rows['spread'] = otm_rows['ask']-otm_rows['bid']
            max_row = otm_rows.loc[otm_rows['spread'].idxmin()]
            strikePrice = max_row['strikePrice']
            askPrice = max_row['ask']
            oi = max_row['openInterest']
            Volume = max_row['totalVolume']
            print("{} has minimum bid-ask spread at Strike : {}, AskPrice: {}, OI : {}, Volume: {} ".format(symbol,strikePrice, askPrice, oi, Volume))
            return max_row
        except Exception as e:
            print('Error in function getOptionGoodSpread: ',e)

                
    def getQuotes(self, symbol):
        try:
            out = self._session.get_quotes(symbol)
            out_str =  out.json()
            stock_info = out_str[symbol]
            last_price = out_str[symbol]['lastPriceInDouble']
            print("Last price of {} is {}".format(symbol, last_price))
            return last_price, stock_info
            
        except Exception as e:
            print('Error in function getQuotes: ',e)