
import Gsheet.google_sheet as google_sheet
from algos import Breakout, Pullback
from tradier_api import *


import requests
#from datetime import datetime
import datetime
import pandas as pd
import time,sys,os,json

from utils import PrintException

DBG_USER_INPUT = False
DBG_BROKER_ORDERS = False


with open('settings.json') as f:
    settings_data = json.load(f)
    LOOP_TIME = settings_data['loop_time']  # seconds
    SEND_SMS = settings_data['send_sms']
    ignore_time = settings_data["ignore_time"]


sheet = google_sheet.gsheet("rake-gsheet-prints.json","Prints")


start_time = datetime.time(settings_data["start_time"])
end_time = datetime.time(settings_data["end_time"])


if __name__ == '__main__':
    try:
        continue_loop = True
        print("---Reading  Gsheet File------")
        df = sheet.read_df('test')

        df_symbols = list(df['ticker'])

        while (continue_loop):
            
            # ----------------------------- #
            timestamp = datetime.datetime.now(pytz.timezone('America/Chicago')).time()
            print("||||||||||||||||Current Time : ", timestamp)

            if not DBG_USER_INPUT:
                stock_prices= get_quotes(df_symbols)
                print(stock_prices)
            
            if (start_time < timestamp <= end_time) or (ignore_time == False):
                #Plug your code here
                objs_dict =[]
                for index, row in df.iterrows():
                    row_dict = df.iloc[index].to_dict()

                    #Get current data
                    if DBG_USER_INPUT:
                        current_price = float(input("Please enter stock input price: "))
                    else:
                        current_price = stock_prices.loc[index, 'last']
                        #print(current_price)
                                        
                    #Create object
                    if row['tradetype'] == 'Breakout':
                        x = Breakout(current_price = current_price, **row_dict)
                    else:
                        x = Pullback(current_price = current_price, **row_dict)

                    # Excute Order
                    order = x.execute(current_price)
                    if order is not None:
                        print(vars(order))
                        print(vars(x))
                    
                    if not DBG_BROKER_ORDERS:
                        print(x.ticker)
                        #if (order is not None) and ((x.real_order == False) | (x.real_order == "") | ((x.real_order == "real"))):
                        if (order is not None) and (x.real_order.lower() in ['', 'real', 'true']):
                            stock_order(**order.__dict__)
                        
                    #Update Trade Data
                    current_obj = vars(x)
                    objs_dict.append(current_obj)

                #Update Spreadsheet
                df = pd.DataFrame(objs_dict)
                print(df)
                sheet.write_df('test',df)
                print("=====Going to sleep===")
                continue_loop = True
            print(LOOP_TIME - (time.time() % LOOP_TIME))
            time.sleep(LOOP_TIME - (time.time() % LOOP_TIME))

    except KeyboardInterrupt:
        print('Program Interrupted through keyboard')

    except KeyError as e:
        cause = e.args[0]
        print('Can not find key : {}'.format(cause))

    except Exception as e:
        PrintException()
        #print("Error :", e)
        
    finally:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
