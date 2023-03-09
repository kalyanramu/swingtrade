DBG_USER_INPUT = False
DBG_BROKER_ORDERS = False

import datetime, pytz
import pandas as pd
#from datetime import datetime
from tradier_api import stock_order, get_quotes
from algos import Breakout, Pullback
import time
import asyncio
import Gsheet.google_sheet as google_sheet

class BackgroundRunner:
    def __init__(self, class_settings, gsheet_info):
        self.value = 0
        self.start_time = class_settings["start_time"]
        self.end_time = class_settings["end_time"]
        self.loop_time = class_settings["loop_time"]
  
        self.continue_loop = True
        #self.sheet = google_sheet.gsheet("testgsheets-creds.json","Prints")
        self.spreadsheet_name = gsheet_info['spreadsheet_name']
        self.worksheet_name = gsheet_info['worksheet_name']
        self.credentials_file = gsheet_info['credentials_file']
        self.read_data = True
        if self.read_data:
            self.sheet = google_sheet.gsheet(self.credentials_file, self.spreadsheet_name)
            self.df = self.sheet.read_df(self.worksheet_name)
            self.read_data = False
        #df_symbols = list(set(df['ticker']))
        self.df_symbols = list(self.df['ticker'])
        print('Finished Background Task Initialization...')
        self.iterations = 0

    async def run_main(self):
        while (self.continue_loop):
            
            # ----------------------------- #
            timestamp = datetime.datetime.now(pytz.timezone('America/Chicago')).time()
            
            print("||||||||||||||||Current Time : ", timestamp)

            if self.read_data:
                self.sheet = google_sheet.gsheet(self.credentials_file, self.spreadsheet_name)
                self.df = self.sheet.read_df(self.worksheet_name)
                self.read_data = False

            if not DBG_USER_INPUT:
                stock_prices= get_quotes(self.df_symbols)
                print(stock_prices)
            
            if self.start_time < timestamp <= self.end_time:
                #Plug your code here
                objs_dict =[]
                for index, row in self.df.iterrows():
                    row_dict = self.df.iloc[index].to_dict()

                    #Get current data
                    if DBG_USER_INPUT:
                        current_price = float(input("Please enter stock input price: "))
                    else:
                        current_price = stock_prices.loc[index, 'last']
                        #print(current_price)
                    
                    #Create object
                    if row['tradetype'] == 'Breakout':
                        x = Breakout(current_price  = current_price,**row_dict)
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
                self.df = pd.DataFrame(objs_dict)
                print(self.df)
                self.sheet.write_df(self.worksheet_name,self.df)
                self.iterations +=1
                print("=====Going to sleep===")
                #continue_loop = True

            print(self.loop_time - (time.time() % self.loop_time))
            #time.sleep(self.loop_time - (time.time() % LOOP_TIME))
            await asyncio.sleep(self.loop_time - (time.time() % self.loop_time))
            print(self.continue_loop)
            if (self.continue_loop == False):
                    print('Shutting down background task...')
            #await asyncio.sleep(0.1)
        
