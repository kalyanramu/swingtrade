import twelvedata
from datetime import datetime, timedelta
import pytz
class TwelveDataService(twelvedata.TDClient):
    def __init__(self, consumer_key):
        self._key = consumer_key
        #print(consumer_key)
        super().__init__(consumer_key)

    def test_connection(self):
        print(f'Accessing Twelve Data with {self._key}')

    def get_intraday(self, symbols, time_period, output_size=100):
        interval = str(time_period)+"min"
        ts = self.time_series(symbol=symbols,interval=interval,outputsize=output_size,timezone="America/Chicago")
        return ts.as_pandas()

    def get_latest_close(self, symbols, time_period=1):
        df = self.get_intraday(symbols, time_period,output_size=5)
        #print(df)
        out = [float(df.loc[symbol]['close'][0]) for symbol in symbols]
        #print(out)
        return out
    
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

class TwelveDataServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, twelvedata_client_key, **_ignored):
        if not self._instance:
            consumer_key = self.authorize(twelvedata_client_key)
            self._instance = TwelveDataService(twelvedata_client_key)
        return self._instance

    def authorize(self, key):
        return key


