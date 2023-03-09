#from DataBrokers.databroker import DataBroker
from DataBrokers import databroker
# TDA Test
# from config_tda_api import tda_api_key
# tda_config = {
#     'tda_client_key': tda_api_key,
# }

# tda_broker = databroker.services.create('TDA', **tda_config)

# #Test Quotes
# out = tda_broker.get_quotes(['AMZN','AAPL'])
# print(out['AMZN'])
# print(out['AAPL'])


# #Test Intraday Data
# out = tda_broker.get_intraday_history('AAPL', time_period =5)
# print(out)

# #Test Latest Close
# out = tda_broker.get_latest_close('AAPL', time_period =1)
# print(out)

# Tradier Test

from DataBrokers.config_tradier_api import tradier_api_key, tradier_account_id
tradier_config = {
    'tradier_client_key': tradier_api_key,
    'tradier_account_id': tradier_account_id
}
tradier_broker = databroker.services.create('TRADIER', **tradier_config)

out = tradier_broker.get_quotes(['AAPL','SPY'])
print(out['AAPL'])

out = tradier_broker.get_intraday_history('AAPL', time_period =5)
print(out)

out = tradier_broker.get_latest_close('AAPL', time_period =1)
print(out)