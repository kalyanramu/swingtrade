from object_factory import ObjectFactory
#from twelvedata_service import TwelveDataServiceBuilder
#from tdadata_service import TDADataServiceBuilder
from tradierdata_service import TradierDataServiceBuilder

import pytz
import datetime
class DataBroker:
    def get_current_day(self, offset=0):
        print(datetime.now())
        date = datetime.now(pytz.timezone('America/Chicago'))
        date = date - datetime.timedelta(days=offset)
        date_str = date.strftime("%Y-%m-%d")
        return date_str

    def OR_time_str_cst(self):
        today = self.get_current_day()
        OR_time_str = today + " " + "08:30:00-05:00"
        return OR_time_str

    def get_current_time_cst(self):
        time = datetime.now(pytz.timezone('America/Chicago')).strftime("%Y-%m-%d %H:%M:%S")
        return time

    def get_intraday(self, symbols,time_period, output_size):
        pass
    
    def get_daily(self, symbols):
        pass

    def get_quotes(self,symbols):
        pass

    def get_latest_close(self, symbols, time_period):
        pass

    def test_connection(self):
        pass

class DataServiceProvider(ObjectFactory):
    def get(self, service_id, **kwargs):
        return self.create(service_id, **kwargs)

services = DataServiceProvider()
#services.register_builder('TWELVE_DATA', TwelveDataServiceBuilder())
services.register_builder('TRADIER', TradierDataServiceBuilder())
#services.register_builder('TDA', TDADataServiceBuilder())
