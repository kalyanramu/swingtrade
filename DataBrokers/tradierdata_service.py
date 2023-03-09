from datetime import datetime, timedelta
import pytz
import requests
import pandas as pd
eastern = pytz.timezone('US/Eastern')

class TradierDataService():
    def __init__(self, consumer_key, account_id):
        self._key = consumer_key
        self._accountid = account_id
        self._quotes_url = 'https://api.tradier.com/v1/markets/quotes'
        self._optionchain_url = 'https://api.tradier.com/v1/markets/options/chains'
        self._expirations_url = 'https://api.tradier.com/v1/markets/options/expirations'
        self._orderexec_url = 'https://api.tradier.com/v1/accounts/'+ account_id +'/orders'
        self._timesales_url = 'https://api.tradier.com/v1/markets/timesales'

    def test_connection(self):
        print(f'Accessing Tradier Data with {self._key}')

    def get_quotes(self, symbols):
        symbols_str = ','.join(symbols)
        #print(symbols_str)
        response = requests.get(self._quotes_url,
            params={'symbols': symbols_str},
            headers={'Authorization': 'Bearer '+ self._key, 'Accept': 'application/json'}
            )
        json_response = response.json()
        #print("quotes: ", json_response)
        df = pd.DataFrame(json_response['quotes']['quote'])
        out = {}
        for index, row in df.iterrows():
            out[row['symbol']] = row['last']
        return out

    def get_intraday_history(self, symbol, time_period, output_size=100, NDays=5, extended_hours = False):
        try:
            tradier_session_filter = 'all' if extended_hours else 'open'
            offset = timedelta(days = 0)
            period = time_period
            symbol = symbol.upper()

            if type(period) is int:
                interval = str(period)+'min'
            else:
                interval = period

            stop_time = self._get_current_time()
            stop_time_est = stop_time.astimezone(eastern)
            stop_time_str  = stop_time_est.strftime("%Y-%m-%d %H:%M")
            start_time = stop_time - timedelta(days=NDays)
            start_time_est = start_time.astimezone(eastern)
            start_time_str = start_time_est.strftime("%Y-%m-%d %H:%M")
                    
            params=   {'symbol': symbol, 
                        'interval': interval, 
                        'start': start_time_str, 
                        'end': stop_time_str, 
                        'session_filter': tradier_session_filter
                        }
            
            headers = {'Authorization': 'Bearer '+ self._key, 'Accept': 'application/json'}
            response = requests.get(self._timesales_url, params = params, headers = headers)
            #print(response)
            json_response = response.json()

            if json_response['series'] is None:
                msg = ('Invalid arguments to API Call for get_historical_intraday(): Check Symbol or time, symbol : {}').format(symbol)
                raise Exception(msg)
            else:
                df = pd.DataFrame(json_response['series']['data'])
                df.rename(columns={'timestamp':'datetime', 'time': 'localtime'}, inplace=True)
                df['datetime'] *= 1000
                #df = df.assign(localtime = pd.to_datetime(df['datetime'], unit='ms'))
                #df['localtime'] = df['localtime'].dt.tz_localize('UTC').dt.tz_convert('America/Chicago')
                #print(df)
                return df
            
        except Exception as e:
            print("Error in function get_intraday", e)
            return None

    def get_latest_close(self, symbol, time_period=1):
        try:
            df = self.get_intraday_history(symbol, time_period,output_size=5)
            #print(df)
            out = float(df['close'].iloc[-1])
            #print(out)
            return out

        except Exception as e:
            print("Error in tradierdata_service.get_latest_close", e)
            return None

    
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

    def _get_current_time(self):
        time = datetime.now(pytz.timezone('America/Chicago'))
        return time

class TradierDataServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, tradier_client_key,tradier_account_id, **_ignored):
        if not self._instance:
            consumer_key = self.authorize(tradier_client_key)
            account_id = tradier_account_id
            self._instance = TradierDataService(consumer_key,account_id)
        return self._instance

    def authorize(self, key):
        return key


